import contextlib
import io
import json
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

from renee.src.renee.util import renee_base, update_cluster_partition


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


def test_update_cluster_partition_success():
    """Test successfully updating cluster.json partition."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Set up test directory structure
        config_dir = os.path.join(tmp_dir, "config")
        os.makedirs(config_dir)
        cluster_json_path = os.path.join(config_dir, "cluster.json")
        
        # Create a valid cluster.json
        cluster_data = {
            "__default__": {
                "partition": "norm",
                "mem": "8g",
                "threads": "1"
            },
            "some_rule": {
                "mem": "16g"
            }
        }
        with open(cluster_json_path, "w") as fh:
            json.dump(cluster_data, fh, indent=4, sort_keys=True)
        
        # Update the partition
        update_cluster_partition(tmp_dir, "long")
        
        # Verify the update
        with open(cluster_json_path, "r") as fh:
            updated_data = json.load(fh)
        
        assert updated_data["__default__"]["partition"] == "long"
        assert updated_data["__default__"]["mem"] == "8g"  # Other fields unchanged
        assert updated_data["some_rule"]["mem"] == "16g"  # Other rules unchanged


def test_update_cluster_partition_with_context():
    """Test that context appears in error messages when provided."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Don't create cluster.json - should raise FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            update_cluster_partition(tmp_dir, "long", context="after initialization")
        
        assert "after initialization" in str(exc_info.value)
        assert "cluster.json" in str(exc_info.value)


def test_update_cluster_partition_file_not_found():
    """Test FileNotFoundError when cluster.json doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "config"))
        # Don't create cluster.json
        
        with pytest.raises(FileNotFoundError) as exc_info:
            update_cluster_partition(tmp_dir, "short")
        
        assert "cluster.json" in str(exc_info.value)


def test_update_cluster_partition_malformed_json():
    """Test RuntimeError when cluster.json contains malformed JSON."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_dir = os.path.join(tmp_dir, "config")
        os.makedirs(config_dir)
        cluster_json_path = os.path.join(config_dir, "cluster.json")
        
        # Write malformed JSON
        with open(cluster_json_path, "w") as fh:
            fh.write("{invalid json content")
        
        with pytest.raises(RuntimeError) as exc_info:
            update_cluster_partition(tmp_dir, "long")
        
        assert "Malformed JSON" in str(exc_info.value)
        assert "cluster.json" in str(exc_info.value)


def test_update_cluster_partition_missing_default_section():
    """Test KeyError when cluster.json is missing __default__ section."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_dir = os.path.join(tmp_dir, "config")
        os.makedirs(config_dir)
        cluster_json_path = os.path.join(config_dir, "cluster.json")
        
        # Create cluster.json without __default__ section
        cluster_data = {
            "some_rule": {
                "partition": "norm",
                "mem": "16g"
            }
        }
        with open(cluster_json_path, "w") as fh:
            json.dump(cluster_data, fh, indent=4, sort_keys=True)
        
        with pytest.raises(KeyError) as exc_info:
            update_cluster_partition(tmp_dir, "long")
        
        assert "__default__" in str(exc_info.value)
        assert "cluster.json" in str(exc_info.value)


def test_update_cluster_partition_preserves_formatting():
    """Test that the function preserves JSON formatting (indent=4, sort_keys=True)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_dir = os.path.join(tmp_dir, "config")
        os.makedirs(config_dir)
        cluster_json_path = os.path.join(config_dir, "cluster.json")
        
        # Create a cluster.json with multiple keys to verify sorting
        cluster_data = {
            "__default__": {
                "partition": "norm",
                "mem": "8g",
                "threads": "1"
            },
            "z_rule": {"mem": "16g"},
            "a_rule": {"mem": "32g"}
        }
        with open(cluster_json_path, "w") as fh:
            json.dump(cluster_data, fh, indent=4, sort_keys=True)
        
        # Update the partition
        update_cluster_partition(tmp_dir, "long")
        
        # Read the raw file content to check formatting
        with open(cluster_json_path, "r") as fh:
            content = fh.read()
        
        # Verify indentation (4 spaces)
        assert '    "__default__"' in content
        # Verify sorting: a_rule should come before z_rule
        a_pos = content.index('"a_rule"')
        z_pos = content.index('"z_rule"')
        assert a_pos < z_pos
