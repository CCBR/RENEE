import os
import sys

from ccbr_tools.pipeline.util import _cp_r_safe_, _sym_safe_

from .util import update_cluster_partition


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
        update_cluster_partition(
            output_path,
            sub_args.partition,
            context="after initialization"
        )

    # Create renamed symlinks to rawdata
    inputs = _sym_safe_(input_data=sub_args.input, target=output_path)

    return inputs
