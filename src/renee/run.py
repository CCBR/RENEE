import contextlib
import io
import json
import os
import pathlib
import sys
from ccbr_tools.pipeline.util import get_hpcname, get_tmp_dir

from .util import renee_base
from .conditions import fatal
from .initialize import initialize
from .setup import setup
from .dryrun import dryrun
from .orchestrate import orchestrate


def run(sub_args):
    """Initialize, setup, and run the RENEE pipeline.
    Calls initialize() to create output directory and copy over pipeline resources,
    setup() to create the pipeline config file, dryrun() to ensure their are no issues
    before running the pipeline, and finally run() to execute the Snakemake workflow.
    @param sub_args <parser.parse_args() object>:
        Parsed arguments for run sub-command
    """
    # Get PATH to RENEE git repository for copying over pipeline resources

    # hpcname is either biowulf, frce, or blank
    hpcname = get_hpcname()
    if sub_args.runmode == "init" or not os.path.exists(
        os.path.join(sub_args.output, "config.json")
    ):
        # Initialize working directory, copy over required pipeline resources
        input_files = initialize(
            sub_args, repo_path=renee_base(), output_path=sub_args.output
        )

        # Step pipeline for execution, create config.json config file from templates
        config = setup(
            sub_args,
            ifiles=input_files,
            repo_path=renee_base(),
            output_path=sub_args.output,
        )
    # load config from existing file
    else:
        with open(os.path.join(sub_args.output, "config.json"), "r") as config_file:
            config = json.load(config_file)

    # ensure the working dir is read/write friendly
    scripts_path = os.path.join(sub_args.output, "workflow", "scripts")
    os.chmod(scripts_path, 0o755)

    # Optional Step: Dry-run pipeline
    if sub_args.dry_run:
        dryrun_output = dryrun(
            outdir=sub_args.output
        )  # python3 returns byte-string representation
        print("\nDry-running RENEE pipeline:\n{}".format(dryrun_output.decode("utf-8")))
        # sys.exit(0) # DONT exit now ... exit after printing singularity bind paths

    # determine "wait"
    wait = ""
    if sub_args.wait:
        wait = "--wait"

    # Resolve all Singularity Bindpaths
    rawdata_bind_paths = config["project"]["datapath"]

    # Get FastQ Screen Database paths
    # and other reference genome file paths
    fqscreen_cfg1 = config["bin"]["rnaseq"]["tool_parameters"]["FASTQ_SCREEN_CONFIG"]
    fqscreen_cfg2 = config["bin"]["rnaseq"]["tool_parameters"]["FASTQ_SCREEN_CONFIG2"]
    fq_screen_paths = get_fastq_screen_paths(
        [
            os.path.join(sub_args.output, fqscreen_cfg1),
            os.path.join(sub_args.output, fqscreen_cfg2),
        ]
    )
    kraken_db_path = [config["bin"]["rnaseq"]["tool_parameters"]["KRAKENBACDB"]]
    genome_bind_paths = resolve_additional_bind_paths(
        list(config["references"]["rnaseq"].values()) + fq_screen_paths + kraken_db_path
    )
    all_bind_paths = "{},{}".format(",".join(genome_bind_paths), rawdata_bind_paths)

    if sub_args.dry_run:  # print singularity bind baths and exit
        print("\nSingularity Bind Paths:{}".format(all_bind_paths))
        # end at dry run
    else:  # continue with real run
        # Run pipeline
        masterjob = orchestrate(
            mode=sub_args.mode,
            outdir=sub_args.output,
            additional_bind_paths=all_bind_paths,
            alt_cache=sub_args.singularity_cache,
            threads=sub_args.threads,
            tmp_dir=get_tmp_dir(sub_args.tmp_dir, sub_args.output),
            wait=wait,
            hpcname=hpcname,
        )

        # Wait for subprocess to complete,
        # this is blocking
        masterjob.wait()

        # Relay information about submission
        # of the master job or the exit code of the
        # pipeline that ran in local mode
        if sub_args.mode == "local":
            if int(masterjob.returncode) == 0:
                print("{} pipeline has successfully completed".format("RENEE"))
            else:
                fatal(
                    "{} pipeline failed. Please see standard output for more information.".format(
                        "RENEE"
                    )
                )
        elif sub_args.mode == "slurm":
            jobid = (
                open(os.path.join(sub_args.output, "logfiles", "mjobid.log"))
                .read()
                .strip()
            )
            if int(masterjob.returncode) == 0:
                print("Successfully submitted master job: ", end="")
            else:
                fatal(
                    "Error occurred when submitting the master job. Error code = {}".format(
                        masterjob.returncode
                    )
                )
            print(jobid)


def resolve_additional_bind_paths(search_paths):
    """Finds additional singularity bind paths from a list of random paths. Paths are
    indexed with a compostite key containing the first two directories of an absolute
    file path to avoid issues related to shared names across the /gpfs shared network
    filesystem. For each indexed list of file paths, a common path is found. Assumes
    that the paths provided are absolute paths, the renee build sub command creates
    resource file index with absolute filenames.
    @param search_paths list[<str>]:
        List of absolute file paths to find common bind paths from
    @return common_paths list[<str>]:
        Returns a list of common shared file paths to create additional singularity bind paths
    """
    common_paths = []
    indexed_paths = {}

    for ref in search_paths:
        # Skip over resources with remote URI and
        # skip over strings that are not file PATHS as
        # RENEE build creates absolute resource PATHS
        if (
            ref.lower().startswith("sftp://")
            or ref.lower().startswith("s3://")
            or ref.lower().startswith("gs://")
            or not ref.lower().startswith(os.sep)
        ):
            continue

        # Break up path into directory tokens
        for r in [
            ref,
            str(pathlib.Path(ref).resolve()),
        ]:  # taking care of paths which are symlinks!
            path_list = os.path.abspath(r).split(os.sep)

            try:  # Create composite index from first two directories
                # Avoids issues created by shared /gpfs/ PATHS
                index = path_list[1:3]
                index = tuple(index)
            except IndexError:
                index = path_list[1]  # ref startswith /
            if index not in indexed_paths:
                indexed_paths[index] = []
            # Create an INDEX to find common PATHS for each root child directory
            # like /scratch or /data. This prevents issues when trying to find the
            # common path between these two different directories (resolves to /)
            indexed_paths[index].append(str(os.sep).join(path_list))

    for index, paths in indexed_paths.items():
        # Find common paths for each path index
        common_paths.append(os.path.dirname(os.path.commonprefix(paths)))

    return list(set(common_paths))


def get_fastq_screen_paths(fastq_screen_confs, match="DATABASE", file_index=-1):
    """Parses fastq_screen.conf files to get the paths of each fastq_screen database.
    This path contains bowtie2 indices for reference genome to screen against.
    The paths are added as singularity bind points.
    @param fastq_screen_confs list[<str>]:
        Name of fastq_screen config files to parse
    @param match <string>:
        Keyword to indicate a line match [default: 'DATABASE']
    @param file_index <int>:
        Index of line line containing the fastq_screen database path
    @return list[<str>]:
        Returns a list of fastq_screen database paths
    """
    databases = []
    for file in fastq_screen_confs:
        with open(file, "r") as fh:
            for line in fh:
                if line.startswith(match):
                    db_path = line.strip().split()[file_index]
                    databases.append(db_path)
    return databases
