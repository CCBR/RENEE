import contextlib
import io
import os
import pathlib
import tempfile

from renee.src.renee.util import (
    renee_base,
    _cp_r_safe_,
)


def test_renee_base():
    renee_bin = renee_base(os.path.join("bin", "renee"))
    assert renee_bin.endswith("/bin/renee") and os.path.exists(renee_bin)


def test_cp_safe():
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = os.path.join(tmp_dir, "testout")
        os.makedirs(os.path.join(outdir, "config"))
        pathlib.Path(os.path.join(outdir, "config", "tmp.txt")).touch()
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            _cp_r_safe_(
                source=renee_base(),
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
                source=renee_base(),
                target=outdir,
                resources=["config"],
                safe_mode=False,
            )
        assert not stdout.getvalue() and "config.yaml" in os.listdir(configdir)
