import argparse
import glob
import os
import tempfile

from ccbr_tools.pipeline.util import (
    get_tmp_dir,
    get_hpcname,
)
from ccbr_tools.pipeline.cache import get_sif_cache_dir
from ccbr_tools.shell import exec_in_context

from renee.src.renee.util import renee_base, get_shared_resources_dir
from renee.src.renee.run import run


def test_dryrun():
    if get_hpcname() == "biowulf":
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_args = argparse.Namespace(
                input=list(glob.glob(renee_base(".tests", "*.fastq.gz"))),
                output=tmp_dir,
                genome=renee_base("config", "genomes", "biowulf", "hg38_36.json"),
                mode="slurm",
                runmode="run",
                dry_run=True,
                sif_cache=get_sif_cache_dir(),
                singularity_cache=os.environ["SINGULARITY_CACHEDIR"],
                tmp_dir=tmp_dir,
                shared_resources=get_shared_resources_dir(None),
                star_2_pass_basic=False,
                small_rna=False,
                create_nidap_folder=False,
                wait=False,
                threads=2,
            )
            # execute dry run and capture stdout/stderr
            allout = exec_in_context(run, run_args)
        assert (
            "This was a dry-run (flag -n). The order of jobs does not reflect the order of execution."
            in allout
        )
