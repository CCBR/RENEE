import pytest
import subprocess

renee_run = (
    "src/renee/__main__.py run "
    "--mode local --runmode init --dry-run "
    "--input .tests/*.fastq.gz "
    "--genome hg38_30 "
)


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
