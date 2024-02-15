import pytest
import subprocess
from src.renee.__main__ import exists


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
