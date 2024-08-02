import contextlib
import io
import os
import pathlib
import tempfile

from renee.src.renee.__main__ import build

renee_build = (
    "src/renee/__main__.py build "
    "--dry-run "
    "--ref-name test "
    "--ref-fa .tests/KO_S3.R1.fastq.gz "
    "--ref-gtf .tests/KO_S3.R1.fastq.gz "
    "--gtf-ver 0 "
)
