import json
import os
import subprocess
import tempfile

# These tests exercise the lightweight path where resources are copied
# and cluster.json is updated from the CLI --partition option.


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
        "--input .tests/*.fastq.gz --partition long"
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
