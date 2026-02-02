import json
import os
import pathlib

from ccbr_tools.pipeline.util import get_hpcname


def renee_base(*paths, debug=False):
    """Get the absolute path to a file in the repository
    @return abs_path <str>
    """
    src_file = pathlib.Path(__file__).absolute()
    if debug:
        print("SRC FILE:", src_file)
    basedir = src_file.parent.parent.parent
    return str(basedir.joinpath(*paths))


def get_version(debug=False):
    """Get the current RENEE version
    @return version <str>
    """
    version_file = renee_base("VERSION")
    if debug:
        print("VERSION FILE:", version_file)
    with open(version_file, "r") as vfile:
        version = f"v{vfile.read().strip()}"
    return version


def get_shared_resources_dir(shared_dir, hpc=get_hpcname()):
    """Get default shared resources directory for biowulf and frce. Allow user override."""
    if not shared_dir:
        if hpc == "biowulf":
            shared_dir = (
                "/data/CCBR_Pipeliner/Pipelines/RENEE/resources/shared_resources"
            )
        elif hpc == "frce":
            shared_dir = "/mnt/projects/CCBR-Pipelines/pipelines/RENEE/resources/shared_resources"
    return shared_dir


def update_cluster_partition(output_path, partition, context=""):
    """Update the default partition in cluster.json.
    
    Reads cluster.json from the output directory, updates the __default__ partition,
    and writes it back with proper formatting.
    
    @param output_path <str>:
        Path to the output directory containing config/cluster.json
    @param partition <str>:
        The partition name to set in cluster.json
    @param context <str>:
        Optional context string for error messages (e.g., "after initialization")
    @raises FileNotFoundError: If cluster.json doesn't exist
    @raises RuntimeError: If cluster.json is malformed JSON
    @raises KeyError: If cluster.json is missing the __default__ section
    """
    cluster_json = os.path.join(output_path, "config", "cluster.json")
    context_msg = f" {context}" if context else ""
    
    if not os.path.exists(cluster_json):
        raise FileNotFoundError(
            f"Expected cluster.json at '{cluster_json}'{context_msg}"
        )
    
    with open(cluster_json, "r") as fh:
        try:
            cluster_cfg = json.load(fh)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Malformed JSON in cluster.json at '{cluster_json}'"
            ) from e
    
    if "__default__" not in cluster_cfg:
        raise KeyError(
            f"cluster.json missing '__default__' section at '{cluster_json}'"
        )
    
    cluster_cfg["__default__"]["partition"] = partition
    
    with open(cluster_json, "w") as fh:
        json.dump(cluster_cfg, fh, indent=4, sort_keys=True)
