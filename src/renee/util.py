import json
import os
import pathlib

from ccbr_tools.pipeline.util import get_hpcname

# Known QOS/partition resource limits on supported HPCs.
# Used by enforce_partition_limits() to cap per-rule cluster.json values so
# SLURM does not reject individual jobs that exceed partition maximums.
# "max_walltime_sec" is in seconds for internal comparison only.
PARTITION_LIMITS = {
    ("biowulf", "student"): {
        "max_walltime_sec": 8 * 3600,  # 8 hours
        "max_walltime_str": "8:00:00",
        "max_cpus": 32,
    },
}


def _walltime_to_seconds(walltime_str):
    """Convert a SLURM walltime string to total seconds.

    Accepts the formats: HH:MM:SS, MM:SS, D-HH:MM:SS.

    @param walltime_str <str>: SLURM walltime string.
    @return seconds <int>
    @raises ValueError: If the format is unrecognised.
    """
    s = walltime_str.strip()
    days = 0
    if "-" in s:
        day_part, s = s.split("-", 1)
        days = int(day_part)
    parts = s.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    elif len(parts) == 2:
        hours, minutes, seconds = 0, int(parts[0]), int(parts[1])
    else:
        raise ValueError(f"Unrecognised SLURM walltime format: '{walltime_str}'")
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def enforce_partition_limits(output_path, partition, hpc=None, context=""):
    """Cap per-rule walltime and CPU values in cluster.json to the known limits
    of the requested SLURM partition, so that individual jobs are not rejected
    by the scheduler.

    Rules whose time or CPU requests exceed the partition maximum are silently
    reduced to that maximum; a UserWarning is emitted for each capped value so
    the user is informed.

    If the (hpc, partition) combination is not in PARTITION_LIMITS, this
    function is a no-op — it only enforces limits for known partitions.

    @param output_path <str>:
        Path to the output directory containing config/cluster.json.
    @param partition <str>:
        The SLURM partition name (e.g. "student", "norm").
    @param hpc <str|None>:
        HPC name (e.g. "biowulf"). Defaults to get_hpcname() when None.
    @param context <str>:
        Optional context string for error messages.
    @raises FileNotFoundError: If cluster.json doesn't exist.
    @raises RuntimeError: If cluster.json is malformed JSON.
    @raises KeyError: If cluster.json is missing the __default__ section.
    """
    if hpc is None:
        hpc = get_hpcname()

    limits = PARTITION_LIMITS.get((hpc, partition))
    if limits is None:
        return

    max_walltime_sec = limits["max_walltime_sec"]
    max_walltime_str = limits["max_walltime_str"]
    max_cpus = limits["max_cpus"]

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

    capped_walltimes = []
    capped_cpus = []

    for rule, rule_cfg in cluster_cfg.items():
        if not isinstance(rule_cfg, dict):
            continue

        # Cap walltime
        if "time" in rule_cfg:
            try:
                rule_secs = _walltime_to_seconds(rule_cfg["time"])
            except ValueError:
                continue
            if rule_secs > max_walltime_sec:
                capped_walltimes.append(rule)
                rule_cfg["time"] = max_walltime_str

        # Cap CPU count (stored as either "threads" or "cpus-per-task")
        for cpu_key in ("threads", "cpus-per-task"):
            if cpu_key in rule_cfg:
                try:
                    rule_cpus = int(rule_cfg[cpu_key])
                except ValueError:
                    continue
                if rule_cpus > max_cpus:
                    capped_cpus.append((rule, cpu_key, rule_cfg[cpu_key]))
                    rule_cfg[cpu_key] = str(max_cpus)

    with open(cluster_json, "w") as fh:
        json.dump(cluster_cfg, fh, indent=4, sort_keys=True)

    if capped_walltimes:
        rule_list = ", ".join(capped_walltimes)
        print(
            f"\n[!] {partition} partition: {len(capped_walltimes)} rule walltime(s) "
            f"capped to {max_walltime_str}"
            f"\n    Affected rules: {rule_list}"
            f"\n    Note: some jobs may not finish within {max_walltime_str} "
            f"for large datasets."
        )
    if capped_cpus:
        cpu_list = ", ".join(f"{r} ({k}={v})" for r, k, v in capped_cpus)
        print(
            f"[!] {partition} partition: CPU requests capped to {max_cpus} for: {cpu_list}"
        )


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


def update_cluster_time(output_path, walltime, context=""):
    """Update the default walltime in cluster.json.

    Reads cluster.json from the output directory, updates the __default__ time,
    and writes it back with proper formatting.

    @param output_path <str>:
        Path to the output directory containing config/cluster.json
    @param walltime <str>:
        The walltime to set in cluster.json (for example: 4-00:00:00 or 12:00:00)
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

    cluster_cfg["__default__"]["time"] = walltime

    with open(cluster_json, "w") as fh:
        json.dump(cluster_cfg, fh, indent=4, sort_keys=True)
