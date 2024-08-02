#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""RENEE: Rna sEquencing aNalysis pipElinE:
An highly reproducible and portable RNA-seq data analysises pipeline
About:
    This is the main entry for the RENEE pipeline.
USAGE:
	$ renee <run|build|unlock|cache> [OPTIONS]
Example:
    $ renee run --input .tests/*.R?.fastq.gz --output /data/$USER/RNA_hg38 --genome hg38_30 --mode slurm
"""

# Python standard library
from __future__ import print_function
from shutil import copy
import json
import os
import subprocess
import sys
import textwrap

# 3rd party imports from pypi
import argparse

# local imports
from .cache import get_sif_cache_dir
from .run import run
from .dryrun import dryrun
from .gui import launch_gui
from .conditions import fatal
from .util import (
    get_hpcname,
    get_tmp_dir,
    get_genomes_list,
    get_version,
    check_python_version,
)

# Pipeline Metadata and globals
RENEE_PATH = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
__version__ = get_version()
__home__ = os.path.dirname(os.path.abspath(__file__))
_name = os.path.basename(sys.argv[0])
_description = "a highly-reproducible RNA-seq pipeline"
check_python_version()


class Colors:
    """Class encoding for ANSI escape sequences for styling terminal text.
    Any string that is formatting with these styles must be terminated with
    the escape sequence, i.e. `Colors.end`.
    """

    # Escape sequence
    end = "\33[0m"
    # Formatting options
    bold = "\33[1m"
    italic = "\33[3m"
    url = "\33[4m"
    blink = "\33[5m"
    highlighted = "\33[7m"
    # Text Colors
    black = "\33[30m"
    red = "\33[31m"
    green = "\33[32m"
    yellow = "\33[33m"
    blue = "\33[34m"
    pink = "\33[35m"
    cyan = "\33[96m"
    white = "\33[37m"
    # Background fill colors
    bg_black = "\33[40m"
    bg_red = "\33[41m"
    bg_green = "\33[42m"
    bg_yellow = "\33[43m"
    bg_blue = "\33[44m"
    bg_pink = "\33[45m"
    bg_cyan = "\33[46m"
    bg_white = "\33[47m"


def permissions(parser, filename, *args, **kwargs):
    """Checks permissions using os.access() to see the user is authorized to access
    a file/directory. Checks for existence, readability, writability and executability via:
    os.F_OK (tests existence), os.R_OK (tests read), os.W_OK (tests write), os.X_OK (tests exec).
    @param parser <argparse.ArgumentParser() object>:
        Argparse parser object
    @param filename <str>:
        Name of file to check
    @return filename <str>:
        If file exists and user can read from file
    """
    if not os.path.exists(filename):
        parser.error(
            "File '{}' does not exists! Failed to provide valid input.".format(filename)
        )

    if not os.access(filename, *args, **kwargs):
        parser.error(
            "File '{}' exists, but cannot read file due to permissions!".format(
                filename
            )
        )

    return filename


def check_cache(parser, cache, *args, **kwargs):
    """Check if provided SINGULARITY_CACHE is valid. Singularity caches cannot be
    shared across users (and must be owned by the user). Singularity strictly enforces
    0700 user permission on on the cache directory and will return a non-zero exitcode.
    @param parser <argparse.ArgumentParser() object>:
        Argparse parser object
    @param cache <str>:
        Singularity cache directory
    @return cache <str>:
        If singularity cache dir is valid
    """
    if not os.path.exists(cache):
        # Cache directory does not exist on filesystem
        os.makedirs(cache)
    elif os.path.isfile(cache):
        # Cache directory exists as file, raise error
        parser.error(
            """\n\t\x1b[6;37;41mFatal: Failed to provided a valid singularity cache!\x1b[0m
        The provided --singularity-cache already exists on the filesystem as a file.
        Please run {} again with a different --singularity-cache location.
        """.format(
                sys.argv[0]
            )
        )
    elif os.path.isdir(cache):
        # Provide cache exists as directory
        # Check that the user owns the child cache directory
        # May revert to os.getuid() if user id is not sufficient
        if (
            os.path.exists(os.path.join(cache, "cache"))
            and os.stat(os.path.join(cache, "cache")).st_uid != os.getuid()
        ):
            # User does NOT own the cache directory, raise error
            parser.error(
                """\n\t\x1b[6;37;41mFatal: Failed to provided a valid singularity cache!\x1b[0m
                The provided --singularity-cache already exists on the filesystem with a different owner.
                Singularity strictly enforces that the cache directory is not shared across users.
                Please run {} again with a different --singularity-cache location.
                """.format(
                    sys.argv[0]
                )
            )

    return cache


def unlock(sub_args):
    """Unlocks a previous runs output directory. If snakemake fails ungracefully,
    it maybe required to unlock the working directory before proceeding again.
    This is rare but it does occasionally happen. Maybe worth add a --force
    option to delete the '.snakemake/' directory in the future.
    @param sub_args <parser.parse_args() object>:
        Parsed arguments for unlock sub-command
    """
    print("Unlocking the pipeline's output directory...")
    outdir = sub_args.output

    try:
        unlock_output = subprocess.check_output(
            ["snakemake", "--unlock", "--cores", "1", "--configfile=config.json"],
            cwd=outdir,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        # Unlocking process returned a non-zero exit code
        sys.exit("{}\n{}".format(e, e.output))

    print("Successfully unlocked the pipeline's working directory!")


def _sym_refs(input_data, target, make_copy=False):
    """Creates symlinks for each reference file provided
    as input. If a symlink already exists, it will not try to create a new symlink.
    If relative source PATH is provided, it will be converted to an absolute PATH.
    If a symlink is provided in input_data, the canocial path of the symlink is found
    to avoid any future singularity binding issues. A physical copy of the data can
    be created by setting make_copy to True (default behavior is to create a symlink).
    copy of a file can be created
    @param input_data <list[<str>]>:
        List of input files to symlink to target location
    @param target <str>:
        Target path to create sylink (output directory)
    @param make_copy <boolean>:
        Create a physical copy of data (Default: False)
    @return canocial_input_paths list[<str>]:
        List of canonical paths for the list of input files (added to singularity bindpaths)
    """
    # Find canocial paths of input files for adding to singularity bindpaths
    canocial_input_paths = []
    for file in input_data:
        target_name = os.path.join(os.path.abspath(target), os.path.basename(file))
        source_name = os.path.abspath(os.path.realpath(file))
        canocial_input_paths.append(os.path.dirname(source_name))

        if not os.path.exists(target_name):
            if not make_copy:
                # Create a symlink if it does not already exist
                # Follow source symlinks to resolve any binding issues
                os.symlink(source_name, target_name)
            else:
                # Create a physical copy if it does not already exist
                copy(file, os.path.abspath(target))

    return list(set(canocial_input_paths))


def _configure(sub_args, filename, git_repo):
    """Private function for configure_build() that creates the build.yml
    from user inputs.
    @param sub_args <parser.parse_args() object>:
        Parsed arguments for unlock sub-command
    @params filename <str>:
        Output filename of build config YAML file
    @param git_repo <str>:
        Path to renee github repository installation
    """
    # Save config to output directory
    print("\nGenerating config file in '{}'... ".format(filename), end="")
    # Resolves if an image needs to be pulled from an OCI registry or
    # a local SIF generated from the renee cache subcommand exists
    sif_config = image_cache(sub_args, {})
    # Creates config file /path/to/output/config/build.yml
    with open(filename, "w") as fh:
        fh.write('GENOME: "{}"\n'.format(sub_args.ref_name))
        fh.write(
            'REFFA: "{}"\n'.format(
                os.path.join(sub_args.output, os.path.basename(sub_args.ref_fa))
            )
        )
        fh.write(
            'GTFFILE: "{}"\n'.format(
                os.path.join(sub_args.output, os.path.basename(sub_args.ref_gtf))
            )
        )
        fh.write('GTFVER: "{}"\n'.format(sub_args.gtf_ver))
        fh.write('OUTDIR: "{}"\n'.format(sub_args.output))
        fh.write('SCRIPTSDIR: "{}/workflow/scripts/builder"\n'.format(sub_args.output))
        fh.write('BUILD_HOME: "{}"\n'.format(git_repo))
        fh.write('SMALL_GENOME: "{}"\n'.format(sub_args.small_genome))
        fh.write('TMP_DIR: "{}"\n'.format(sub_args.tmp_dir))
        fh.write('SHARED_RESOURCES: "{}"\n'.format(sub_args.shared_resources))
        # fh.write('READLENGTHS:\n')
        # read_lengths = ['50', '75', '100', '125', '150']
        # for rl in read_lengths:
        #     fh.write('  - {}\n'.format(rl))
        # Add singularity images URIs or local SIFs
        # Converts a nested json file to yaml format
        for k in sif_config.keys():
            fh.write("{}: \n".format(k))
            for tag, uri in sif_config[k].items():
                fh.write('  {}: "{}"\n'.format(tag, uri))
    print("Done!")


def _reset_write_permission(target):
    os.system("chmod -R u+w,g-w,o-w " + target)


def configure_build(sub_args, git_repo, output_path):
    """Setups up working directory for build option and creates config file (build.yml)
    @param git_repo <str>:
        Path to renee github repository installation
    @param output_path <str>:
        Path to build output directory
    @param sub_args <parser.parse_args() object>:
        Parsed arguments for build sub-command
    @return additional_bind_paths list[<str>]:
        List of canonical paths for the list of input files to be added singularity bindpath
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

    # Copy over templates are other required resources, overwriting if they exist
    _cp_r_safe_(
        source=git_repo,
        target=output_path,
        resources=["workflow", "resources", "config"],
        safe_mode=False,
    )
    _reset_write_permission(target=output_path)
    _configure(
        sub_args=sub_args,
        filename=os.path.join(output_path, "config", "build.yml"),
        git_repo=git_repo,
    )
    additional_bind_paths = _sym_refs(
        input_data=[sub_args.ref_fa, sub_args.ref_gtf],
        target=output_path,
        make_copy=False,
    )

    return additional_bind_paths


def build(sub_args):
    """Builds the reference files for the RENEE pipeline from a genomic FASTA
    file and a GTF file. Disclaimer: hybrid genomes not supported.
    @param sub_args <parser.parse_args() object>:
        Parsed arguments for unlock sub-command
    """
    # Get PATH to RENEE git repository
    # for copying over pipeline resources

    # Build Output directory
    output_path = os.path.abspath(sub_args.output)

    # Configure build output directory,
    # initialize, copy resources, and
    # generate config file
    additional_bind_paths = configure_build(
        sub_args=sub_args, git_repo=RENEE_PATH, output_path=output_path
    )

    # Add any additional bindpaths
    if sub_args.shared_resources:
        # Check if shared resource path
        # needs to be added to bindlist
        if not sub_args.shared_resources in additional_bind_paths:
            additional_bind_paths.append(sub_args.shared_resources)

    additional_bind_paths = ",".join(additional_bind_paths)

    # determine "wait"
    wait = ""
    if sub_args.wait:
        wait = "--wait"

    # hpcname is either biowulf, frce, or blank
    hpcname = get_hpcname()

    # Dryrun pipeline
    if sub_args.dry_run:
        dryrun_output = dryrun(
            outdir=output_path,
            config=os.path.join("config", "build.yml"),
            snakefile=os.path.join("workflow", "rules", "build.smk"),
        )

        print(
            "\nDry-running RENEE Reference building pipeline:\n{}".format(
                dryrun_output.decode("utf-8")
            )
        )
        sys.exit(0)

    # Run RENEE reference building pipeline
    masterjob = orchestrate(
        mode="slurm",
        outdir=output_path,
        additional_bind_paths=additional_bind_paths,
        alt_cache=sub_args.singularity_cache,
        submission_script="builder",
        masterjob="pl:build",
        tmp_dir=get_tmp_dir(sub_args.tmp_dir, sub_args.output),
        wait=wait,
        hpcname=hpcname,
    )

    masterjob.wait()

    # Relay information about submission
    # of the master job or the exit code of the
    # pipeline that ran in local mode
    sub_args.mode = "slurm"
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
            open(os.path.join(sub_args.output, "logfiles", "bjobid.log")).read().strip()
        )
        if int(masterjob.returncode) == 0:
            print("Successfully submitted master job: ", end="")
        else:
            fatal("Error occurred when submitting the master job.")
        print(jobid)


def cache(sub_args):
    """Caches remote resources or reference files stored on DockerHub and S3.
    Local SIFs will be created from images defined in 'config/containers/images.json'.
    @TODO: add option to cache other shared S3 resources (i.e. kraken db and fqscreen indices)
    @param sub_args <parser.parse_args() object>:
        Parsed arguments for unlock sub-command
    """
    sif_cache = sub_args.sif_cache
    # Get absolute PATH to templates in renee git repo
    repo_path = os.path.dirname(os.path.abspath(__file__))
    images = os.path.join(repo_path, "config", "containers", "images.json")

    # Create image cache
    if not os.path.exists(sif_cache):
        # Pipeline output directory does not exist on filesystem
        os.makedirs(sif_cache)
    elif os.path.exists(sif_cache) and os.path.isfile(sif_cache):
        # Provided Path for pipeline output directory exists as file
        raise OSError(
            """\n\tFatal: Failed to create provided sif cache directory!
        User provided --sif-cache PATH already exists on the filesystem as a file.
        Please {} cache again with a different --sif-cache PATH.
        """.format(
                sys.argv[0]
            )
        )

    # Check if local SIFs already exist on the filesystem
    with open(images, "r") as fh:
        data = json.load(fh)

    pull = []
    for image, uri in data["images"].items():
        sif = os.path.join(
            sif_cache, "{}.sif".format(os.path.basename(uri).replace(":", "_"))
        )
        if not os.path.exists(sif):
            # If local sif does not exist on in cache, print warning
            # and default to pulling from URI in config/containers/images.json
            print('Image will be pulled from "{}".'.format(uri), file=sys.stderr)
            pull.append(uri)

    if not pull:
        # Nothing to do!
        print("Singularity image cache is already up to update!")
    else:
        # There are image(s) that need to be pulled
        if not sub_args.dry_run:
            # submission_script for renee cache is /path/to/output/resources/cacher
            # Quote user provided values to avoid shell injections
            username = os.environ.get("USER", os.environ.get("USERNAME"))
            masterjob = subprocess.Popen(
                "sbatch --parsable -J pl:cache --time=10:00:00 --mail-type=BEGIN,END,FAIL "
                + str(os.path.join(repo_path, "resources", "cacher"))
                + " slurm "
                + " -s '{}' ".format(sif_cache)
                + " -i '{}' ".format(",".join(pull))
                + " -t '{0}/{1}/.singularity/' ".format(sif_cache, username),
                cwd=sif_cache,
                shell=True,
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE,
            )

            masterjob.communicate()
            print(
                "RENEE reference cacher submitted master job with exit-code: {}".format(
                    masterjob.returncode
                )
            )


def genome_options(parser, user_option, prebuilt):
    """Dynamically checks if --genome option is a valid choice. Compares against a
    list of prebuilt or bundled genome reference genomes and accepts a custom reference
    genome that was built using the 'renee build' command. The ability to also
    accept a custom reference JSON file allows for chaining of the renee build and run
    commands in succession.
    @param parser <argparse.ArgumentParser object>:
        Parser object from which an exception is raised not user_option is not valid
    @param user_option <str>:
        Provided value to the renee run, --genome argument
    @param prebuilt list[<str>]:
        List of prebuilt reference genomes
    return user_option <str>:
        Provided value to the renee run, --genome argument
        If value is not valid or custom reference genome JSON file not readable,
        an exception is raised.
    """
    # Checks for custom built genomes using renee build
    if user_option.endswith(".json"):
        # Check file is readable or accessible
        permissions(parser, user_option, os.R_OK)
    # Checks against valid pre-built options
    # TODO: makes this more dynamic in the future to have it check against
    # a list of genomes (files) in config/genomes/*.json
    elif user_option not in prebuilt:
        # User did NOT provide a valid choice
        parser.error(
            """provided invalid choice, '{}', to --genome argument!\n
        Choose from one of the following pre-built genome options: \n
        \t{}\n
        or supply a custom reference genome JSON file generated from renee build.
        """.format(
                user_option, prebuilt
            )
        )

    return user_option


def parsed_arguments(name, description):
    """Parses user-provided command-line arguments. Requires argparse and textwrap
    package. argparse was added to standard lib in python 3.2 and textwrap was added
    in python 3.5. To create custom help formatting for subparsers a docstring is
    used create the help message for required options. argparse does not support named
    subparser groups, which is normally what would be used to accomphish this reformatting.
    As so, the help message for require options must be suppressed. If a new required arg
    is added to a subparser, it must be added to the docstring and the usage statement
    also must be updated.
    @param name <str>:
        Name of the pipeline or command-line tool
    @param description <str>:
        Short description of pipeline or command-line tool
    """
    # Add styled name and description
    c = Colors
    styled_name = "{0}RENEE{1}".format(c.bold, c.end)
    description = "{0}{1}{2}".format(c.bold, description, c.end)

    # Create a top-level parser
    parser = argparse.ArgumentParser(
        description="{}: {}".format(styled_name, description)
    )

    # Adding Version information
    parser.add_argument(
        "--version", action="version", version="renee {}".format(__version__)
    )

    # Create sub-command parser
    subparsers = parser.add_subparsers(help="List of available sub-commands")

    # Options for the "run" sub-command
    # Grouped sub-parser arguments are currently not supported by argparse.
    # https://bugs.python.org/issue9341
    # Here is a work around to create more useful help message for named
    # options that are required! Please note: if a required arg is added the
    # description below should be updated (i.e. update usage and add new option)
    required_run_options = textwrap.dedent(
        """
        {1}{0} {3}run{4}: {1} Runs the data-processing and quality-control pipeline.{4}

        {1}{2}Synopsis:{4}
          $ {0} run [--help] \\
                              [--small-rna] [--star-2-pass-basic] \\
                              [--dry-run] [--mode {{slurm, local}}] \\
                              [--shared-resources SHARED_RESOURCES] \\
                              [--singularity-cache SINGULARITY_CACHE] \\
                              [--sif-cache SIF_CACHE] \\
                              [--tmp-dir TMP_DIR] \\
                              [--wait] \\
                              [--create-nidap-folder] \\
                              [--threads THREADS] \\
                              --input INPUT [INPUT ...] \\
                              --output OUTPUT \\
                              --genome {{hg38_30, mm10_M21}}

        {1}{2}Description:{4}
          To run the pipeline with with your data, please provide a space separated
        list of FastQs (globbing is supported), an output directory to store results,
        and a reference genome.

          Optional arguments are shown in square brackets above. Please visit our docs
        at "https://CCBR.github.io/RENEE/" for more information, examples, and
        guides.

        {1}{2}Required arguments:{4}
          --input INPUT [INPUT ...]
                                Input FastQ file(s) to process. One or more FastQ files
                                can be provided. The pipeline supports single-end and
                                pair-end RNA-seq data.
                                  Example: --input .tests/*.R?.fastq.gz

          --output OUTPUT
                                Path to an output directory. This location is where
                                the pipeline will create all of its output files, also
                                known as the pipeline's working directory. If the user
                                provided working directory has not been initialized,
                                it will be created automatically.
                                  Example: --output /data/$USER/RNA_hg38

          --genome {{hg38_30,mm10_M21,custom.json}}
                                Reference genome. This option defines the reference
                                genome of the samples. RENEE does comes bundled with
                                pre built reference files for human and mouse samples;
                                however, it is worth noting that the pipeline can accept
                                custom reference genomes created with the build sub
                                command. Here is a list of available pre built genomes:
                                hg38_30 or mm10_M21. hg38_30 uses the GENCODE version 30
                                human annotation, while mm10_M21 uses GENCODE version M21
                                mouse annotation. A custom reference genome created with
                                the build sub command can also be provided. The name of
                                this custom reference JSON file is dependent on the
                                values provided to the following renee build args
                                '--ref-name REF_NAME --gtf-ver GTF_VER', where the name
                                of the output file uses the following naming convention:
                                '{{REF_NAME}}_{{GTF_VER}}.json'.
                                  Example: --genome hg38_30

        {1}{2}Analysis options:{4}
          --small-rna           Uses ENCODE's recommendations for small RNA. This
                                option should be used with small RNA libraries. These
                                are rRNA-depleted libraries that have been size
                                selected to be shorter than 200bp. Size selection
                                enriches for small RNA species such as miRNAs, siRNAs,
                                or piRNAs. This option is only supported with single-
                                end data. This option should not be combined with the
                                star 2-pass basic option.
                                  Example: --small-rna

          --star-2-pass-basic   Run STAR in per sample 2-pass mapping mode. It is
                                recommended to use this option when processing a set
                                of unrelated samples. It is not adivsed to use this
                                option for a study with multiple related samples. By
                                default, the pipeline ultilizes a multi sample 2-pass
                                mapping approach where the set of splice junctions
                                detected across all samples are provided to the second
                                pass of STAR. This option overrides the default
                                behavior so each sample will be processed in a per
                                sample two-pass basic mode. This option should not be
                                combined with the small RNA option.
                                  Example: --star-2-pass-basic

        {1}{2}Orchestration options:{4}
          --dry-run             Does not execute anything. Only displays what steps in
                                the pipeline remain or will be run.
                                  Example: --dry-run

          --mode {{slurm,local}}
                                Method of execution. Defines the mode of execution.
                                Valid options for this mode include: local or slurm.
                                Additional modes of execution are coming soon, default:
                                slurm.
                                Here is a brief description of each mode:
                                   • local: uses local method of execution. local runs
                                will run serially on compute instance. This is useful
                                for testing, debugging, or when a users does not have
                                access to a  high  performance  computing environment.
                                If this option is not provided, it will default to a
                                slurm mode of execution.
                                   • slurm: uses slurm execution backend. This method
                                will submit jobs to a  cluster  using sbatch. It is
                                recommended running the pipeline in this mode as it
                                will be significantly faster.
                                  Example: --mode slurm

          --shared-resources SHARED_RESOURCES
                                Local path to shared resources. The pipeline uses a set
                                of shared reference files that can be re-used across ref-
                                erence genomes. These currently include reference files
                                for kraken and FQScreen. These reference files can be
                                downloaded with the build sub command's --shared-resources
                                option. These files only need to be downloaded once. If
                                you are running the pipeline on Biowulf, you do NOT need
                                to download these reference files! They already exist on
                                the filesystem in a location that anyone can access. If
                                you are running the pipeline on another cluster or target
                                system, you will need to download the shared resources
                                with the build sub command, and you will need to provide
                                this option to the run sub command every time. Please
                                provide the same path that was provided to the build sub
                                command's --shared-resources option.
                                  Example: --shared-resources /data/shared/renee

          --singularity-cache SINGULARITY_CACHE
                                Overrides the $SINGULARITY_CACHEDIR variable. Images
                                from remote registries are cached locally on the file
                                system. By default, the singularity cache is set to:
                                '/path/to/output/directory/.singularity/'. Please note
                                that this cache cannot be shared across users.
                                  Example: --singularity-cache /data/$USER

          --sif-cache SIF_CACHE
                                Path where a local cache of SIFs are stored. This cache
                                can be shared across users if permissions are properly
                                setup. If a SIF does not exist in the SIF cache, the
                                image will be pulled from Dockerhub. {0} cache
                                sub command can be used to create a local SIF cache.
                                Please see {0} cache for more information.
                                   Example: --sif-cache /data/$USER/sifs/

          --wait
                                Wait until master job completes. This is required if
                                the job is submitted using HPC API. If not provided
                                the API may interpret submission of master job as
                                completion of the pipeline!

          --create-nidap-folder
                                Create folder called "NIDAP" with file to-be-moved back to NIDAP
                                This makes it convenient to move only this folder (called NIDAP)
                                and its content back to NIDAP, rather than the entire pipeline
                                output folder.

          --tmp-dir TMP_DIR
                                Path on the file system for writing temporary output
                                files. By default, the temporary directory is set to
                                '/lscratch/$SLURM_JOBID' on NIH's Biowulf cluster and
                                'OUTPUT' on the FRCE cluster.
                                However, if you are running the pipeline on another cluster,
                                this option will need to be specified.
                                Ideally, this path should point to a dedicated location on
                                the filesystem for writing tmp files.
                                On many systems, this location is
                                set to somewhere in /scratch. If you need to inject a
                                variable into this string that should NOT be expanded,
                                please quote this options value in single quotes.
                                  Example: --tmp-dir '/cluster_scratch/$USER/'
          --threads THREADS
                                Max number of threads for local processes. It is
                                recommended setting this value to the maximum number
                                of CPUs available on the host machine, default: 2.
                                  Example: --threads: 16

        {1}{2}Misc Options:{4}
          -h, --help            Show usage information, help message, and exit.
                                  Example: --help
        """.format(
            "renee", c.bold, c.url, c.italic, c.end
        )
    )

    # Display example usage in epilog
    run_epilog = textwrap.dedent(
        """
        {2}{3}Example:{4}
          # Step 1.) Grab an interactive node,
          # do not run on head node and add
          # required dependencies to $PATH
          srun -N 1 -n 1 --time=1:00:00 --mem=8gb  --cpus-per-task=2 --pty bash
          module purge
          module load singularity snakemake

          # Step 2A.) Dry run pipeline with provided test data
          ./{0} run --input .tests/*.R?.fastq.gz \\
                         --output /data/$USER/RNA_hg38 \\
                         --genome hg38_30 \\
                         --mode slurm \\
                         --dry-run

          # Step 2B.) Run RENEE pipeline
          # The slurm mode will submit jobs to the cluster.
          # It is recommended running renee in this mode.
          ./{0} run --input .tests/*.R?.fastq.gz \\
                         --output /data/$USER/RNA_hg38 \\
                         --genome hg38_30 \\
                         --mode slurm

        {2}{3}Ver:{4}
          {1}

        {2}{3}Prebuilt genome+annotation combos:{4}
          {5}
        """.format(
            "renee", __version__, c.bold, c.url, c.end, list(get_genomes_list())
        )
    )

    # Suppressing help message of required args to overcome no sub-parser named groups
    subparser_run = subparsers.add_parser(
        "run",
        help="Run the RENEE pipeline with your FastQ files.",
        usage=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=required_run_options,
        epilog=run_epilog,
        add_help=False,
    )

    subparser_gui = subparsers.add_parser(
        "gui",
        help="Launch the RENEE pipeline with a Graphical User Interface (GUI)",
        description="",
    )

    # Required Arguments
    # Input FastQ files
    subparser_run.add_argument(
        "--input",
        # Check if the file exists and if it is readable
        type=lambda file: permissions(parser, file, os.R_OK),
        required=True,
        nargs="+",
        help=argparse.SUPPRESS,
    )

    # Output Directory,
    # analysis working directory
    subparser_run.add_argument(
        "--output",
        type=lambda option: os.path.abspath(os.path.expanduser(option)),
        required=True,
        help=argparse.SUPPRESS,
    )

    # Reference Genome, used for dynamically
    # selecting reference files
    subparser_run.add_argument(
        "--genome",
        required=True,
        type=lambda option: str(
            genome_options(subparser_run, option, get_genomes_list())
        ),
        help=argparse.SUPPRESS,
    )

    # Optional Arguments
    # Add custom help message
    subparser_run.add_argument("-h", "--help", action="help", help=argparse.SUPPRESS)

    # Analysis options
    # Run STAR 2-pass-basic
    subparser_run.add_argument(
        "--star-2-pass-basic",
        action="store_true",
        required=False,
        default=False,
        help=argparse.SUPPRESS,
    )

    # Run pipeline using ENCODE's recommendations
    # for small RNA processing
    subparser_run.add_argument(
        "--small-rna",
        action="store_true",
        required=False,
        default=False,
        help=argparse.SUPPRESS,
    )

    # Orchestration options
    # Dry-run, do not execute the workflow,
    # prints what steps remain
    subparser_run.add_argument(
        "--dry-run",
        action="store_true",
        required=False,
        default=False,
        help=argparse.SUPPRESS,
    )
    subparser_run.add_argument(
        "--runmode",
        # Determines how to run the pipeline: init, run
        # TODO: this API is different from XAVIER & CARLISLE, which have a --runmode=dryrun option instead of a --dry-run flag.
        required=False,
        default="run",
        choices=["init", "run"],
        type=str,
        help=argparse.SUPPRESS,
    )

    # Execution Method, run locally
    # on a compute node or submit to
    # a supported job scheduler, etc.
    subparser_run.add_argument(
        "--mode",
        type=str,
        required=False,
        default="slurm",
        choices=["slurm", "local"],
        help=argparse.SUPPRESS,
    )

    # Path to previously downloaded shared
    # reference files, see build option for
    # more information
    subparser_run.add_argument(
        "--shared-resources",
        type=lambda option: permissions(
            parser, os.path.abspath(os.path.expanduser(option)), os.R_OK
        ),
        required=False,
        default=None,
        help=argparse.SUPPRESS,
    )

    # Singularity cache directory,
    # default uses output directory
    subparser_run.add_argument(
        "--singularity-cache",
        type=lambda option: check_cache(
            parser, os.path.abspath(os.path.expanduser(option))
        ),
        required=False,
        help=argparse.SUPPRESS,
    )

    # Local SIF cache directory,
    # default pulls from Dockerhub
    subparser_run.add_argument(
        "--sif-cache",
        type=lambda option: os.path.abspath(os.path.expanduser(option)),
        required=False,
        help=argparse.SUPPRESS,
        default=get_sif_cache_dir(),
    )

    # Create NIDAP output folder
    subparser_run.add_argument(
        "--create-nidap-folder",
        action="store_true",
        required=False,
        default=False,
        help='Create folder called "NIDAP" with file to-be-moved back to NIDAP \
                                This makes it convenient to move only this folder (called NIDAP) and its content back \
                                to NIDAP, rather than the entire pipeline output folder',
    )

    # wait until master job finishes ... required for HPC API execution
    subparser_run.add_argument(
        "--wait",
        action="store_true",
        required=False,
        default=False,
        help="Wait until master job completes. This is required if \
                                the job is submitted using HPC API. If not provided \
                                the API may interpret submission of master job as \
                                completion of the pipeline!",
    )

    # Base directory to write
    # temporary/intermediate files
    subparser_run.add_argument(
        "--tmp-dir",
        type=str,
        required=False,
        default="",
        help=argparse.SUPPRESS,
    )

    # Number of threads for the
    # pipeline's main proceess
    # This is only applicable for
    # local rules or when running
    # in local mode.
    subparser_run.add_argument(
        "--threads", type=int, required=False, default=2, help=argparse.SUPPRESS
    )

    # Options for the "build" sub-command
    # Grouped sub-parser arguments are currently not supported.
    # https://bugs.python.org/issue9341
    # Here is a work around to create more useful help message for named
    # options that are required! Please note: if a required arg is added the
    # description below should be updated (i.e. update usage and add new option)
    required_build_options = textwrap.dedent(
        """
        {1}{0} {3}build{4}: {1}Builds reference files for the pipeline.{4}

        {1}{2}Synopsis:{4}
          $ {0} build [--help] \\
                                [--shared-resources SHARED_RESOURCES] [--small-genome] \\
                                [--dry-run] [--singularity-cache SINGULARITY_CACHE] \\
                                [--sif-cache SIF_CACHE] [--tmp-dir TMP_DIR] \\
                                --ref-fa REF_FA \\
                                --ref-name REF_NAME \\
                                --ref-gtf REF_GTF \\
                                --gtf-ver GTF_VER \\
                                --wait \\
                                --output OUTPUT

        {1}{2}Description:{4}
          Builds the reference files for the RENEE pipeline from a genomic FASTA
        file and a GTF file. Disclaimer: If you have two GTF files, eg. hybrid genomes
        (viral + host), then you need to create one FASTA and one GTF file for the hybrid
        genome prior to running the renee build command. Reference files built with
        this sub command can be used with renee run sub command.

          Optional arguments are shown in square brackets above. Please visit our docs
        at "https://CCBR.github.io/RENEE/" for more information, examples, and
        guides.

        {1}{2}Required arguments:{4}
          --ref-fa REF_FA
                              Genomic FASTA file of the reference genome. If you are
                              downloading this from GENCODE, you should select the 'PRI'
                              genomic FASTA file. This file will contain the primary
                              genomic assembly (contains chromosomes and scaffolds).
                                Example: --ref-fa GRCh38.primary_assembly.genome.fa
          --ref-name REF_NAME
                              Name of the input reference genome. This is the
                              common name of the reference genome. Here is a list
                              of common examples for different model organisms:
                              mm10, hg38, rn6, danRer11, dm6, canFam3, sacCer3, ce11.
                                Example: --ref-name GRCh38
          --ref-gtf REF_GTF
                              Annotation file or GTF file for the reference genome.
                              If you are downloading this from GENCODE, you should select
                              the 'PRI' GTF file. This file contains gene annotations for
                              the primary assembly (contains chromosomes and scaffolds).
                                Example: --ref-gtf gencode.v41.primary_assembly.gtf
          --gtf-ver GTF_VER
                              Version of the annotation file or GTF file provided.
                              If you are using a GTF file from GENCODE, use the release
                              number or version (i.e. 'M25' for mouse or '37' for human).
                              Visit gencodegenes.org for more details.
                                Example: --gtf-ver 41
          --output OUTPUT
                              Path to an output directory. This location is where the
                              pipeline will create all of its output files. If the user
                              provided working directory does not exist, it will be auto-
                              matically created.
                                Example: --output /data/$USER/refs/GRCh38_41

        {1}{2}Build options:{4}
          --shared-resources SHARED_RESOURCES
                              Path to download shared resources. The pipeline uses a
                              set of shared reference files that can be re-used across
                              reference genomes. These currently include reference files
                              for kraken and FQScreen. With that being said, these files
                              can be downloaded once in a shared or common location. If
                              you are running the pipeline on Biowulf, you do NOT need
                              to download these reference files. They already exist in
                              an accessible location on the filesystem. If you're setting
                              up the pipeline on a new cluster or target system, you will
                              need to provide this option at least one time. The path
                              provided to this option can be provided to the renee
                              run sub command via the --shared-resources option.
                                Example: --shared-resources /data/shared/renee

          --small-genome      Builds a small genome index. For small genomes, it is
                              recommended running STAR with --genomeSAindexNbases value
                              scaled down. This option runs the build pipeline in a
                              mode where it dynamically finds the optimal value based
                              on the following: min(14, log2(GenomeSize)/2 - 1).
                                Example: --small-genome

        {1}{2}Orchestration options:{4}
          --dry-run           Does not execute anything. Only displays what steps in
                              the pipeline remain or will be run.
                                Example: --dry-run

          --singularity-cache SINGULARITY_CACHE
                              Overrides the $SINGULARITY_CACHEDIR variable. Images
                              from remote registries are cached locally on the file
                              system. By default, the singularity cache is set to:
                              '/path/to/output/directory/.singularity/'. Please note
                              that this cache cannot be shared across users.
                                Example: --singularity-cache /data/$USER

          --sif-cache SIF_CACHE
                              Path where a local cache of SIFs are stored. This cache
                              can be shared across users if permissions are properly
                              setup. If a SIF does not exist in the SIF cache, the
                              image will be pulled from Dockerhub. renee cache
                              sub command can be used to create a local SIF cache.
                              Please see renee cache for more information.
                                Example: --sif-cache /data/$USER/sifs/

          --tmp-dir TMP_DIR
                            Path on the file system for writing temporary output
                            files. By default, the temporary directory is set to
                            '/lscratch/$SLURM_JOBID' on NIH's Biowulf cluster and
                            'outdir' on the FRCE cluster.
                            However, if you are running the pipeline on another cluster,
                            this option will need to be specified.
                            Ideally, this path should point to a dedicated location on
                            the filesystem for writing tmp files.
                            On many systems, this location is
                            set to somewhere in /scratch. If you need to inject a
                            variable into this string that should NOT be expanded,
                            please quote this options value in single quotes.
                                Example: --tmp-dir '/cluster_scratch/$USER/'

          --wait
                                Wait until master job completes. This is required if
                                the job is submitted using HPC API. If not provided
                                the API may interpret submission of master job as
                                completion of the pipeline!

        {1}{2}Misc Options:{4}
          -h, --help          Show usage information, help message, and exit.
                                Example: --help
        """.format(
            "renee", c.bold, c.url, c.italic, c.end
        )
    )

    # Display example usage in epilog
    build_epilog = textwrap.dedent(
        """
        {2}{3}Example:{4}
          # Step 1.) Grab an interactive node,
          # do not run on head node and add
          # required dependencies to $PATH
          srun -N 1 -n 1 --time=1:00:00 --mem=8gb  --cpus-per-task=2 --pty bash
          module purge
          module load singularity snakemake

          # Step 2B.) Dry-run the build pipeline
          renee build --ref-fa GRCm39.primary_assembly.genome.fa \\
                         --ref-name mm39 \\
                         --ref-gtf gencode.vM26.annotation.gtf \\
                         --gtf-ver M26 \\
                         --output /data/$USER/refs/mm39_M26 \\
                         --dry-run

          # Step 2A.) Build {0} reference files
          renee build --ref-fa GRCm39.primary_assembly.genome.fa \\
                         --ref-name mm39 \\
                         --ref-gtf gencode.vM26.annotation.gtf \\
                         --gtf-ver M26 \\
                         --output /data/$USER/refs/mm39_M26

        {2}{3}Version:{4}
          {1}

        {2}{3}Prebuilt genome+annotation combos:{4}
          {5}
        """.format(
            "renee", __version__, c.bold, c.url, c.end, list(get_genomes_list())
        )
    )

    # Suppressing help message of required args to overcome no sub-parser named groups
    subparser_build = subparsers.add_parser(
        "build",
        help="Builds the reference files for the RENEE pipeline.",
        usage=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=required_build_options,
        epilog=build_epilog,
        add_help=False,
    )

    # Required arguments
    # Input Genomic FASTA file
    subparser_build.add_argument(
        "--ref-fa",
        # Check if the file exists and if it is readable
        type=lambda file: permissions(parser, file, os.R_OK),
        required=True,
        help=argparse.SUPPRESS,
    )

    # Reference Genome Name
    subparser_build.add_argument(
        "--ref-name", type=str, required=True, help=argparse.SUPPRESS
    )

    # Input Reference GTF file
    subparser_build.add_argument(
        "--ref-gtf",
        # Check if the file exists and if it is readable
        type=lambda file: permissions(parser, file, os.R_OK),
        required=True,
        help=argparse.SUPPRESS,
    )

    # Reference GTF Version
    subparser_build.add_argument(
        "--gtf-ver", type=str, required=True, help=argparse.SUPPRESS
    )

    # Output Directory,
    # build working directory
    subparser_build.add_argument(
        "--output",
        type=lambda option: os.path.abspath(os.path.expanduser(option)),
        required=True,
        help=argparse.SUPPRESS,
    )

    # Optional Arguments
    # Add custom help message
    subparser_build.add_argument("-h", "--help", action="help", help=argparse.SUPPRESS)

    # Dry-run build workflow,
    # do not execute the workflow
    subparser_build.add_argument(
        "--dry-run",
        action="store_true",
        required=False,
        default=False,
        help=argparse.SUPPRESS,
    )

    # Path to download shared refs
    subparser_build.add_argument(
        "--shared-resources",
        type=lambda option: os.path.abspath(os.path.expanduser(option)),
        required=False,
        default=None,
        help=argparse.SUPPRESS,
    )

    # Small Genome build option for STAR
    subparser_build.add_argument(
        "--small-genome",
        action="store_true",
        required=False,
        default=False,
        help=argparse.SUPPRESS,
    )

    # Singularity cache directory,
    # default uses output directory
    subparser_build.add_argument(
        "--singularity-cache",
        type=lambda option: check_cache(
            parser, os.path.abspath(os.path.expanduser(option))
        ),
        required=False,
        help=argparse.SUPPRESS,
    )

    # Local SIF cache directory,
    # default pull from Dockerhub
    subparser_build.add_argument(
        "--sif-cache",
        type=lambda option: os.path.abspath(os.path.expanduser(option)),
        required=False,
        help=argparse.SUPPRESS,
    )

    # Base directory to write
    # temporary/intermediate files
    subparser_build.add_argument(
        "--tmp-dir",
        type=str,
        required=False,
        default="/lscratch/$SLURM_JOBID/",
        help=argparse.SUPPRESS,
    )

    # wait until master job finishes ... required for HPC API execution
    subparser_build.add_argument(
        "--wait",
        action="store_true",
        required=False,
        default=False,
        help="Wait until master job completes. This is required if \
                                the job is submitted using HPC API. If not provided \
                                the API may interpret submission of master job as \
                                completion of the pipeline!",
    )

    # Sub-parser for the "unlock" sub-command
    # Grouped sub-parser arguments are currently
    # not supported: https://bugs.python.org/issue9341
    # Here is a work around to create more useful help message for named
    # options that are required! Please note: if a required arg is added the
    # description below should be updated (i.e. update usage and add new option)
    required_unlock_options = textwrap.dedent(
        """\
        {1}{0} {3}unlock{4}: {1}Unlocks a previous output directory.{4}

        {1}{2}Synopsis:{4}
          $ {0} unlock [--help] --output OUTPUT

        {1}{2}Description:{4}
          If the pipeline fails ungracefully, it maybe required to unlock
        the working directory before proceeding again. Please verify that
        the pipeline is not running before running this command. If the
        pipeline is still running, the workflow manager will report the
        working directory is locked. This is normal behavior. Do NOT run
        this command if the pipeline is still running.

          Optional arguments are shown in square brackets above. Please
        visit our docs at "https://CCBR.github.io/RENEE/" for more
        information, examples, and guides.

        {1}{2}Required arguments:{4}
          --output OUTPUT       Path to a previous run's output directory
                                to unlock. This will remove a lock on the
                                working directory. Please verify that the
                                pipeline is not running before running
                                this command.
                                  Example: --output /data/$USER/output

        {1}{2}Misc Options:{4}
          -h, --help            Show usage information and exit.
                                  Example: --help
        """.format(
            "renee", c.bold, c.url, c.italic, c.end
        )
    )

    # Display example usage in epilog
    unlock_epilog = textwrap.dedent(
        """\
        {2}{3}Example:{4}
          # Step 1.) Grab an interactive node,
          # do not run on head node and add
          # required dependencies to $PATH
          srun -N 1 -n 1 --time=1:00:00 --mem=8gb  --cpus-per-task=2 --pty bash
          module purge
          module load singularity snakemake

          # Step 2.) Unlock output directory of pipeline
          {0} unlock --output /data/$USER/output

        {2}{3}Version:{4}
          {1}
        """.format(
            "renee", __version__, c.bold, c.url, c.end
        )
    )

    # Suppressing help message of required args to overcome no sub-parser named groups
    subparser_unlock = subparsers.add_parser(
        "unlock",
        help="Unlocks a previous runs output directory.",
        usage=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=required_unlock_options,
        epilog=unlock_epilog,
        add_help=False,
    )

    # Required Arguments
    # Output Directory (analysis working directory)
    subparser_unlock.add_argument(
        "--output", type=str, required=True, help=argparse.SUPPRESS
    )

    # Add custom help message
    subparser_unlock.add_argument("-h", "--help", action="help", help=argparse.SUPPRESS)

    # Sub-parser for the "cache" sub-command
    # Grouped sub-parser arguments are
    # not supported: https://bugs.python.org/issue9341
    # Here is a work around to create more useful help message for named
    # options that are required! Please note: if a required arg is added the
    # description below should be updated (i.e. update usage and add new option)
    required_cache_options = textwrap.dedent(
        """\
        {1}{0} {3}cache{4}: {1}Cache software containers locally.{4}

        {1}{2}Synopsis:{4}
          $ {0} cache [--help] [--dry-run] \\
                  --sif-cache SIF_CACHE

        {1}{2}Description:{4}
        Create a local cache of software dependencies hosted on DockerHub.
        These containers are normally pulled onto the filesystem when the
        pipeline runs; however, due to network issues or DockerHub pull
        rate limits, it may make sense to pull the resources once so a
        shared cache can be created. It is worth noting that a singularity
        cache cannot normally be shared across users. Singularity strictly
        enforces that a cache is owned by the user. To get around this
        issue, the cache subcommand can be used to create local SIFs on
        the filesystem from images on DockerHub.

        Optional arguments are shown in square brackets above. Please visit
        our docs at "https://CCBR.github.io/RENEE/" for more info,
        examples, and guides.

        {1}{2}Required arguments:{4}
          --sif-cache SIF_CACHE
                                Path where a local cache of SIFs will be
                                stored. Images defined in containers.json
                                will be pulled into the local filesystem.
                                The path provided to this option can be
                                passed to the --sif-cache option of the
                                run sub command. Please see {0} run
                                sub command for more information.
                                  Example: --sif-cache /data/$USER/cache

        {1}{2}Orchestration options:{4}
          --dry-run             Does not execute anything. Only displays
                                what remote resources would be pulled.
                                  Example: --dry-run

        {1}{2}Misc Options:{4}
          -h, --help            Show usage information and exits.
                                  Example: --help
        """.format(
            "renee", c.bold, c.url, c.italic, c.end
        )
    )

    # Display example usage in epilog
    cache_epilog = textwrap.dedent(
        """\
        {2}Example:{3}
          # Step 1.) Grab an interactive node,
          # do not run on head node and add
          # required dependencies to $PATH
          srun -N 1 -n 1 --time=1:00:00 --mem=8gb  --cpus-per-task=2 --pty bash
          module purge
          module load singularity snakemake

          # Step 2A.) Dry-run cache to see
          # what software containers will
          # be pulled from Dockerhub
          {0} cache --sif-cache /data/$USER/cache \\
                    --dry-run

          # Step 2B.) Cache software containers
          {0} cache --sif-cache /data/$USER/cache

        {2}Version:{3}
          {1}
        """.format(
            "renee", __version__, c.bold, c.end
        )
    )

    # Suppressing help message of required args
    # to overcome no sub-parser named groups
    subparser_cache = subparsers.add_parser(
        "cache",
        help="Cache software containers locally.",
        usage=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=required_cache_options,
        epilog=cache_epilog,
        add_help=False,
    )

    # Required Arguments
    # Output Directory (analysis working directory)
    subparser_cache.add_argument(
        "--sif-cache",
        type=lambda option: os.path.abspath(os.path.expanduser(option)),
        required=True,
        help=argparse.SUPPRESS,
    )

    # Optional Arguments
    # Dry-run cache command (do not pull any remote resources)
    subparser_cache.add_argument(
        "--dry-run",
        action="store_true",
        required=False,
        default=False,
        help=argparse.SUPPRESS,
    )

    # Add custom help message
    subparser_cache.add_argument("-h", "--help", action="help", help=argparse.SUPPRESS)

    # Define handlers for each sub-parser
    subparser_run.set_defaults(func=run)
    subparser_unlock.set_defaults(func=unlock)
    subparser_build.set_defaults(func=build)
    subparser_cache.set_defaults(func=cache)
    subparser_gui.set_defaults(func=launch_gui)

    # Parse command-line args
    args = parser.parse_args()
    return args


def main():
    # Sanity check for usage
    if len(sys.argv) == 1:
        # Nothing was provided
        fatal("Invalid usage: {} [-h] [--version] ...".format("renee"))

    # Collect args for sub-command
    args = parsed_arguments(name=_name, description=_description)

    # Display version information
    print("RENEE ({})".format(__version__))

    # Mediator method to call sub-command's set handler function
    args.func(args)


if __name__ == "__main__":
    main()
