import tempfile
import json
import os.path
import subprocess

renee_run = (
    "src/renee/__main__.py run "
    "--mode local --runmode init --dry-run "
    "--input .tests/*.fastq.gz "
    "--genome config/genomes/biowulf/hg38_30.json "
)


def run_in_temp(command_str):
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = os.path.join(tmp_dir, "testout")
        output = subprocess.run(
            f"{command_str} --output {outdir}",
            capture_output=True,
            shell=True,
            text=True,
        )
        if os.path.exists(os.path.join(outdir, "config.json")):
            with open(os.path.join(outdir, "config.json"), "r") as infile:
                config = json.load(infile)
        else:
            config = None
    return output, config


def test_cache_sif():
    output, config = run_in_temp(f"{renee_run} --sif-cache tests/data/sifs/")
    assertions = [
        config["images"]["arriba"].endswith(
            "tests/data/sifs/ccbr_arriba_2.0.0_v0.0.1.sif"
        ),
        "does not exist in singularity cache" in output.stderr,
    ]
    assert all(assertions)


def test_cache_nosif():
    output, config = run_in_temp(f"{renee_run}")
    assertions = [
        config["images"]["arriba"] == "docker://nciccbr/ccbr_arriba_2.0.0:v0.0.1",
        "The singularity command has to be available" in output.stderr,
    ]
    assert all(assertions)
