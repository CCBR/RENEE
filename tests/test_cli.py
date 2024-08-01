import pytest
import subprocess
import tempfile
import json
import os.path

renee_run = (
    "src/renee/__main__.py run "
    "--mode local --runmode init --dry-run "
    "--input .tests/*.fastq.gz "
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


def test_help():
    output = subprocess.run(
        "src/renee/__main__.py --help", capture_output=True, shell=True, text=True
    ).stdout
    assert "RENEE" in output


def test_version():
    output = subprocess.run(
        "src/renee/__main__.py --version", capture_output=True, shell=True, text=True
    ).stdout
    assert "renee v" in output


def test_run_error():
    assert (
        "the following arguments are required: --output"
        in subprocess.run(
            f"{renee_run}", capture_output=True, shell=True, text=True
        ).stderr
    )


def test_subcommands_help():
    assert all(
        [
            f"renee {cmd } [--help]"
            in subprocess.run(
                f"src/renee/__main__.py {cmd} --help",
                capture_output=True,
                shell=True,
                text=True,
            ).stdout
            for cmd in ["run", "build", "cache", "unlock"]
        ]
    )


def test_default_genome():
    output, config = run_in_temp(renee_run)
    assert all(
        [
            "hg38_36" in config["references"]["rnaseq"]["GENOME"],
            "The singularity command has to be available" in output.stderr,
        ]
    )


def test_genome_param():
    output, config = run_in_temp(f"{renee_run} --genome hg19_19")
    assert all(
        [
            "hg19_19" in config["references"]["rnaseq"]["GENOME"],
            "The singularity command has to be available" in output.stderr,
        ]
    )
