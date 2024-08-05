import argparse
import glob
import os
import tempfile

from renee.src.renee.util import (
    get_tmp_dir,
    get_shared_resources_dir,
    renee_base,
)
from renee.src.renee.cache import get_sif_cache_dir
from renee.src.renee.run import run_in_context
from renee.src.renee.util import get_hpcname


def test_dryrun():
    if get_hpcname() == "biowulf":
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_args = argparse.Namespace(
                input=list(glob.glob(os.path.join(renee_base(".tests"), "*.fastq.gz"))),
                output=tmp_dir,
                genome=os.path.join(
                    renee_base("config"), "genomes", "biowulf", "hg38_36.json"
                ),
                mode="slurm",
                runmode="run",
                dry_run=True,
                sif_cache=get_sif_cache_dir(),
                singularity_cache=os.environ["SINGULARITY_CACHEDIR"],
                tmp_dir=tmp_dir,
                shared_resources=None,
                star_2_pass_basic=False,
                small_rna=False,
                create_nidap_folder=False,
                wait=False,
                threads=2,
            )
            # execute dry run and capture stdout/stderr
            allout = run_in_context(run_args)
        assert (
            "This was a dry-run (flag -n). The order of jobs does not reflect the order of execution."
            in allout
        )
