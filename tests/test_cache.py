import tempfile
import json
import os.path
import subprocess

from ccbr_tools.pipeline.cache import get_sif_cache_dir, get_singularity_cachedir
from ccbr_tools.shell import shell_run

renee_run = (
    "./bin/renee run "
    "--mode local --runmode init --dry-run "
    "--input .tests/*.fastq.gz "
    "--genome config/genomes/biowulf/hg38_30.json "
)


def run_in_temp(command_str):
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = os.path.join(tmp_dir, "testout")
        output = shell_run(f"{command_str} --output {outdir}")
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
        "does not exist in singularity cache" in output,
    ]
    assert all(assertions)


def test_cache_nosif():
    output, config = run_in_temp(f"{renee_run} --sif-cache not/a/path")
    assertions = [
        config["images"]["arriba"] == "docker://nciccbr/ccbr_arriba_2.0.0:v0.0.1"
    ]
    assert all(assertions)


def test_get_sif_cache_dir():
    assertions = [
        "'CCBR_Pipeliner/SIFS' in get_sif_cache_dir('biowulf')",
        "'CCBR-Pipelines/SIFs' in get_sif_cache_dir('frce')",
    ]
    errors = [assertion for assertion in assertions if not eval(assertion)]
    assert not errors, "errors occurred:\n{}".format("\n".join(errors))


def test_get_singularity_cachedir():
    assertions = [
        "get_singularity_cachedir('outdir') == 'outdir/.singularity'",
        "get_singularity_cachedir('outdir', 'cache') == 'cache'",
    ]
    errors = [assertion for assertion in assertions if not eval(assertion)]
    assert not errors, "errors occurred:\n{}".format("\n".join(errors))


def test_cache_in_temp():
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = os.path.join(tmp_dir, "testout")
        output = shell_run(f"./bin/renee cache --sif-cache {outdir} --dry-run")
    assert "Image will be pulled from" in output
