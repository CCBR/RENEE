import os
import stat
import sys

from ccbr_tools.pipeline.util import _cp_r_safe_, _sym_safe_

from .util import (
    update_cluster_partition,
    update_cluster_time,
    enforce_partition_limits,
)


def _ensure_owner_writable(path):
    """Recursively apply owner write (and conditional execute) permissions to
    all files and directories under *path*, equivalent to ``chmod -R u+wX``.

    - Directories always receive owner write + execute (``u+wx``).
    - Files receive owner write; owner execute is added only when any execute
      bit (user/group/other) is already set (``u+wX``).

    This corrects cases where the source installation has restrictive
    permissions (e.g. -r--rw-r-- / dr-xrwxr-x) that get preserved by
    shutil.copytree / _cp_r_safe_, causing PermissionError when RENEE later
    tries to update cluster.json or other config files.

    @param path <str>: Root directory to fix permissions under.
    """
    _ANY_EXEC = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    for dirpath, dirnames, filenames in os.walk(path):
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            mode = os.stat(fpath).st_mode
            new_mode = mode | stat.S_IWUSR
            if mode & _ANY_EXEC:
                new_mode |= stat.S_IXUSR
            os.chmod(fpath, new_mode)
        os.chmod(
            dirpath,
            os.stat(dirpath).st_mode | stat.S_IWUSR | stat.S_IXUSR,
        )


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
        """.format(sys.argv[0])
        )

    # Copy over templates are other required resources
    _cp_r_safe_(
        source=repo_path,
        target=output_path,
        resources=["workflow", "resources", "config"],
    )

    # Ensure the output directory is owner-writable (equivalent to
    # chmod -R u+wX). The pipeline installation may have restrictive
    # permissions (e.g. -r--rw-r-- / dr-xrwxr-x) that _cp_r_safe_ preserves
    # verbatim, causing PermissionError when RENEE later tries to update
    # cluster.json or other config files.
    _ensure_owner_writable(output_path)

    # If a partition was provided, update the copied cluster.json default partition
    if hasattr(sub_args, "partition") and sub_args.partition:
        update_cluster_partition(
            output_path, sub_args.partition, context="after initialization"
        )
        enforce_partition_limits(
            output_path, sub_args.partition, context="after initialization"
        )
    if hasattr(sub_args, "time") and sub_args.time:
        update_cluster_time(output_path, sub_args.time, context="after initialization")

    # Create renamed symlinks to rawdata
    inputs = _sym_safe_(input_data=sub_args.input, target=output_path)

    return inputs
