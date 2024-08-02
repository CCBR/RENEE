import os
import re
import sys

from renee.src.renee.util import (
    _cp_r_safe_,
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

    # Create renamed symlinks to rawdata
    inputs = _sym_safe_(input_data=sub_args.input, target=output_path)

    return inputs


def _sym_safe_(input_data, target):
    """Creates re-named symlinks for each FastQ file provided
    as input. If a symlink already exists, it will not try to create a new symlink.
    If relative source PATH is provided, it will be converted to an absolute PATH.
    @param input_data <list[<str>]>:
        List of input files to symlink to target location
    @param target <str>:
        Target path to copy templates and required resources
    @return input_fastqs list[<str>]:
        List of renamed input FastQs
    """
    input_fastqs = []  # store renamed fastq file names
    for file in input_data:
        filename = os.path.basename(file)
        renamed = os.path.join(target, rename(filename))
        input_fastqs.append(renamed)

        if not os.path.exists(renamed):
            # Create a symlink if it does not already exist
            # Follow source symlinks to resolve any binding issues
            os.symlink(os.path.abspath(os.path.realpath(file)), renamed)

    return input_fastqs


def rename(filename):
    """Dynamically renames FastQ file to have one of the following extensions: *.R1.fastq.gz, *.R2.fastq.gz
    To automatically rename the fastq files, a few assumptions are made. If the extension of the
    FastQ file cannot be inferred, an exception is raised telling the user to fix the filename
    of the fastq files.
    @param filename <str>:
        Original name of file to be renamed
    @return filename <str>:
        A renamed FastQ filename
    """
    # Covers common extensions from SF, SRA, EBI, TCGA, and external sequencing providers
    # key = regex to match string and value = how it will be renamed
    extensions = {
        # Matches: _R[12]_fastq.gz, _R[12].fastq.gz, _R[12]_fq.gz, etc.
        ".R1.f(ast)?q.gz$": ".R1.fastq.gz",
        ".R2.f(ast)?q.gz$": ".R2.fastq.gz",
        # Matches: _R[12]_001_fastq_gz, _R[12].001.fastq.gz, _R[12]_001.fq.gz, etc.
        # Capture lane information as named group
        ".R1.(?P<lane>...).f(ast)?q.gz$": ".R1.fastq.gz",
        ".R2.(?P<lane>...).f(ast)?q.gz$": ".R2.fastq.gz",
        # Matches: _[12].fastq.gz, _[12].fq.gz, _[12]_fastq_gz, etc.
        "_1.f(ast)?q.gz$": ".R1.fastq.gz",
        "_2.f(ast)?q.gz$": ".R2.fastq.gz",
    }

    if filename.endswith(".R1.fastq.gz") or filename.endswith(".R2.fastq.gz"):
        # Filename is already in the correct format
        return filename

    converted = False
    for regex, new_ext in extensions.items():
        matched = re.search(regex, filename)
        if matched:
            # regex matches with a pattern in extensions
            converted = True
            # Try to get substring for named group lane, retain this in new file extension
            # Come back to this later, I am not sure if this is necessary
            # That string maybe static (i.e. always the same)
            # https://support.illumina.com/help/BaseSpace_OLH_009008/Content/Source/Informatics/BS/NamingConvention_FASTQ-files-swBS.htm#
            try:
                new_ext = "_{}{}".format(matched.group("lane"), new_ext)
            except IndexError:
                pass  # Does not contain the named group lane

            filename = re.sub(regex, new_ext, filename)
            break  # only rename once

    if not converted:
        raise NameError(
            """\n\tFatal: Failed to rename provided input '{}'!
        Cannot determine the extension of the user provided input file.
        Please rename the file list above before trying again.
        Here is example of acceptable input file extensions:
          sampleName.R1.fastq.gz      sampleName.R2.fastq.gz
          sampleName_R1_001.fastq.gz  sampleName_R2_001.fastq.gz
          sampleName_1.fastq.gz       sampleName_2.fastq.gz
        Please also check that your input files are gzipped?
        If they are not, please gzip them before proceeding again.
        """.format(
                filename
            )
        )

    return filename
