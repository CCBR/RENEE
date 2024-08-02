import contextlib
import io
import os
import pathlib
import tempfile

from renee.__main__ import _cp_r_safe_

renee_build = (
    "src/renee/__main__.py build "
    "--dry-run "
    "--ref-name test "
    "--ref-fa .tests/KO_S3.R1.fastq.gz "
    "--ref-gtf .tests/KO_S3.R1.fastq.gz "
    "--gtf-ver 0 "
)
RENEE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_cp_safe():
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = os.path.join(tmp_dir, "testout")
        os.makedirs(os.path.join(outdir, "config"))
        pathlib.Path(os.path.join(outdir, "config", "tmp.txt")).touch()
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            _cp_r_safe_(
                source=RENEE_PATH,
                target=outdir,
                resources=["config"],
                safe_mode=True,
            )
        assert "path exists and `safe_mode` is ON, not copying" in stdout.getvalue()


def test_cp_unsafe():
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = os.path.join(tmp_dir, "testout")
        configdir = os.path.join(outdir, "config")
        os.makedirs(configdir)
        pathlib.Path(os.path.join(configdir, "tmp.txt")).touch()
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            _cp_r_safe_(
                source=RENEE_PATH,
                target=outdir,
                resources=["config"],
                safe_mode=False,
            )
        assert not stdout.getvalue() and "config.yaml" in os.listdir(configdir)
