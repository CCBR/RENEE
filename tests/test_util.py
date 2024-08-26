import contextlib
import io
import os
import pathlib
import pytest
import tempfile
import warnings

from ccbr_tools.pipeline.util import (
    _cp_r_safe_,
    get_genomes_dict,
    get_genomes_list,
)

from renee.src.renee.util import renee_base


def test_renee_base():
    renee_bin = renee_base(os.path.join("bin", "renee"))
    assert str(renee_bin).endswith("/bin/renee") and os.path.exists(renee_bin)


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


def test_get_genomes_warnings():
    with warnings.catch_warnings(record=True) as raised_warnings:
        genomes = get_genomes_list(repo_base=renee_base, hpcname="notAnOption")
        assertions = [
            "len(genomes) == 0",
            "len(raised_warnings) == 2",
            "raised_warnings[0].category is UserWarning",
            "raised_warnings[1].category is UserWarning",
            '"Folder does not exist" in str(raised_warnings[0].message)',
            '"No Genome+Annotation JSONs found" in str(raised_warnings[1].message)',
        ]
        scope = locals()  # make local variables available to eval()
        errors = [assertion for assertion in assertions if not eval(assertion, scope)]
    assert not errors, "errors occurred:\n{}".format("\n".join(errors))


def test_get_genomes_error():
    with pytest.raises(UserWarning) as exception_info:
        get_genomes_list(
            repo_base=renee_base, hpcname="notAnOption", error_on_warnings=True
        )
        assert "Folder does not exist" in str(exception_info.value)


def test_get_genomes_biowulf():
    genomes_dict = get_genomes_dict(repo_base=renee_base, hpcname="biowulf")
    assert len(genomes_dict) > 10
