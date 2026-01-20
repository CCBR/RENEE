import os
import json
import sys

from ccbr_tools.pipeline.util import _cp_r_safe_, _sym_safe_


def initialize(sub_args, repo_path, output_path):
    """Initialize the output directory and copy over required pipeline resources.
    If user provides a output directory path that already exists on the filesystem
    as a file (small chance of happening but possible), a OSError is raised. If the
    output directory PATH already EXISTS, it will not try to create the directory.
    If a resource also already exists in the output directory (i.e. output/workflow),
    it will not try to copy over that directory. In the future, it maybe worth adding
    an optional cli arg called --force, that can modify this behavior. Returns a list
    of renamed FastQ files (i.e. renamed symlinks).
    @param sub_args <parser.parse_args() object>:
        Parsed arguments for run sub-command
    @param repo_path <str>:
        Path to RENEE source code and its templates
    @param output_path <str>:
        Pipeline output path, created if it does not exist
    @return inputs list[<str>]:
        List of pipeline's input FastQ files
    """
    if not os.path.exists(output_path):
        # Pipeline output directory does not exist on filesystem
        os.makedirs(output_path)

    elif os.path.exists(output_path) and os.path.isfile(output_path):
        # Provided Path for pipeline output directory exists as file
        raise OSError(
            """\n\tFatal: Failed to create provided pipeline output directory!
        User provided --output PATH already exists on the filesystem as a file.
        Please run {} again with a different --output PATH.
        """.format(
                sys.argv[0]
            )
        )

    # Copy over templates are other required resources
    _cp_r_safe_(
        source=repo_path,
        target=output_path,
        resources=["workflow", "resources", "config"],
    )

    # If a partition was provided, update the copied cluster.json default partition
    if hasattr(sub_args, "partition") and sub_args.partition:
        cluster_json = os.path.join(output_path, "config", "cluster.json")
        if not os.path.exists(cluster_json):
            raise FileNotFoundError(
                f"Expected cluster.json at '{cluster_json}' after initialization"
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
        cluster_cfg["__default__"]["partition"] = sub_args.partition
        with open(cluster_json, "w") as fh:
            json.dump(cluster_cfg, fh, indent=4, sort_keys=True)

    # Create renamed symlinks to rawdata
    inputs = _sym_safe_(input_data=sub_args.input, target=output_path)

    return inputs
