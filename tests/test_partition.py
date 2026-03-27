import json
import os
import pathlib
import subprocess
import tempfile

# These tests exercise the lightweight path where resources are copied
# and cluster.json is updated from the CLI --partition/--time options.


def _run_cmd_in_tmp(command: str):
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = os.path.join(tmp_dir, "out")
        cmd = f"{command} --output {outdir}"
        # We don't assert on return code; init/build may continue to later steps
        # that require more inputs. We only care that cluster.json is updated.
        subprocess.run(cmd, shell=True, capture_output=True, text=True)
        cluster_path = os.path.join(outdir, "config", "cluster.json")
        assert os.path.exists(cluster_path), f"Expected {cluster_path} to exist"
        with open(cluster_path, "r") as fh:
            cluster = json.load(fh)
        return cluster


def test_run_init_partition_overrides_cluster_json():
    # Use runmode init so initialize() executes and copies resources.
    # Provide partition 'long' and verify it's written to cluster.json
    base_cmd = (
        "./main.py run --mode local --runmode init --dry-run "
        "--input .tests/*.fastq.gz --genome config/genomes/biowulf/hg38_38.json --partition long"
    )
    cluster = _run_cmd_in_tmp(base_cmd)
    assert (
        cluster.get("__default__", {}).get("partition") == "long"
    ), "cluster.json __default__.partition should be set to 'long' from CLI"


def test_build_partition_overrides_cluster_json():
    # Build path: copy resources and update cluster.json immediately
    base_cmd = (
        "./main.py build --dry-run "
        "--ref-name test "
        "--ref-fa .tests/KO_S3.R1.fastq.gz "
        "--ref-gtf .tests/KO_S3.R1.fastq.gz "
        "--gtf-ver 0 "
        "--partition short"
    )
    cluster = _run_cmd_in_tmp(base_cmd)
    assert (
        cluster.get("__default__", {}).get("partition") == "short"
    ), "cluster.json __default__.partition should be set to 'short' from CLI"


def test_run_init_time_overrides_cluster_json():
    base_cmd = (
        "./main.py run --mode local --runmode init --dry-run "
        "--input .tests/*.fastq.gz --genome config/genomes/biowulf/hg38_38.json --time 05:30:00"
    )
    cluster = _run_cmd_in_tmp(base_cmd)
    assert (
        cluster.get("__default__", {}).get("time") == "05:30:00"
    ), "cluster.json __default__.time should be set to '05:30:00' from CLI"


def test_build_time_overrides_cluster_json():
    base_cmd = (
        "./main.py build --dry-run "
        "--ref-name test "
        "--ref-fa .tests/KO_S3.R1.fastq.gz "
        "--ref-gtf .tests/KO_S3.R1.fastq.gz "
        "--gtf-ver 0 "
        "--time 01:45:00"
    )
    cluster = _run_cmd_in_tmp(base_cmd)
    assert (
        cluster.get("__default__", {}).get("time") == "01:45:00"
    ), "cluster.json __default__.time should be set to '01:45:00' from CLI"


def _write_executable(path: pathlib.Path, content: str):
    path.write_text(content)
    path.chmod(0o755)


def _run_wrapper_and_collect_sbatch(wrapper_name: str, walltime: str | None = None):
    repo_root = pathlib.Path.cwd()
    wrapper = repo_root / "resources" / wrapper_name

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        fakebin = tmp_path / "fakebin"
        outdir = tmp_path / "out"
        log_file = tmp_path / "sbatch_calls.log"

        fakebin.mkdir(parents=True, exist_ok=True)
        outdir.mkdir(parents=True, exist_ok=True)

        _write_executable(
            fakebin / "singularity",
            "#!/usr/bin/env bash\nexit 0\n",
        )
        _write_executable(
            fakebin / "snakemake",
            "#!/usr/bin/env bash\n"
            'if [[ "${1:-}" == "--version" ]]; then\n'
            '  echo "7.7.0"\n'
            "  exit 0\n"
            "fi\n"
            "exit 0\n",
        )
        _write_executable(
            fakebin / "sbatch",
            "#!/usr/bin/env bash\n"
            'echo "$*" >> "${SBATCH_LOG}"\n'
            'if [[ "$*" == *"--parsable"* ]]; then\n'
            '  echo "12345"\n'
            "else\n"
            '  echo "67890"\n'
            "fi\n"
            "exit 0\n",
        )

        env = os.environ.copy()
        env["PATH"] = f"{fakebin}:{env.get('PATH', '')}"
        env["SBATCH_LOG"] = str(log_file)

        cmd = [
            "bash",
            str(wrapper),
            "slurm",
            "-j",
            "pl:test",
            "-b",
            str(tmp_path),
            "-t",
            str(tmp_path),
            "-o",
            str(outdir),
            "-n",
            "unknown",
            "-p",
            "student",
        ]
        if walltime:
            cmd.extend(["-T", walltime])

        subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)

        assert log_file.exists(), "Expected mocked sbatch to be invoked"
        return log_file.read_text().splitlines()


def _assert_partition_propagated(lines):
    master_calls = [line for line in lines if "--parsable" in line]
    cleanup_calls = [line for line in lines if "pl:clean" in line]

    assert master_calls, "Expected at least one master sbatch submission"
    assert cleanup_calls, "Expected cleanup sbatch submission"
    assert "-p student" in master_calls[0], "Master sbatch command missing '-p student'"
    assert (
        "-p student" in cleanup_calls[0]
    ), "Cleanup sbatch command missing '-p student'"


def _assert_time_propagated(lines, walltime):
    master_calls = [line for line in lines if "--parsable" in line]

    assert master_calls, "Expected at least one master sbatch submission"
    assert (
        f"--time={walltime}" in master_calls[0]
    ), "Master sbatch command missing requested --time override"


def test_runner_partition_propagated_to_sbatch_calls():
    calls = _run_wrapper_and_collect_sbatch("runner")
    _assert_partition_propagated(calls)


def test_builder_partition_propagated_to_sbatch_calls():
    calls = _run_wrapper_and_collect_sbatch("builder")
    _assert_partition_propagated(calls)


def test_runner_time_propagated_to_sbatch_calls():
    calls = _run_wrapper_and_collect_sbatch("runner", walltime="03:00:00")
    _assert_time_propagated(calls, "03:00:00")


def test_builder_time_propagated_to_sbatch_calls():
    calls = _run_wrapper_and_collect_sbatch("builder", walltime="00:45:00")
    _assert_time_propagated(calls, "00:45:00")
