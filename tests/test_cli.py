import pytest
import subprocess
from renee.src.renee.__main__ import main

renee_run = (
    "./bin/renee run "
    "--mode local --runmode init --dry-run "
    "--input .tests/*.fastq.gz "
    "--genome config/genomes/biowulf/hg38_30.json "
)


def test_help():
    output = subprocess.run(
        "./bin/renee --help", capture_output=True, shell=True, text=True
    ).stdout
    assert "RENEE" in output


def test_version():
    output = subprocess.run(
        "./bin/renee --version", capture_output=True, shell=True, text=True
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
                f"./bin/renee {cmd} --help",
                capture_output=True,
                shell=True,
                text=True,
            ).stdout
            for cmd in ["run", "build", "cache", "unlock"]
        ]
    )
