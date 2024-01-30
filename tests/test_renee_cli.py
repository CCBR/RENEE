import pytest
from ..renee import modules_command


def test_modules_noHPC():
    with pytest.raises(ValueError, match="Missing required dependencies") as err_info:
        modules_command("")


def test_modules_biowulf():
    assert (
        modules_command("biowulf")
        == '. "/data/CCBR_Pipeliner/db/PipeDB/Conda/etc/profile.d/conda.sh" && conda activate py311 && module load singularity && module load snakemake'
    )


def test_modules_frce():
    assert (
        modules_command("frce")
        == '. "/mnt/projects/CCBR-Pipelines/resources/miniconda3/etc/profile.d/conda.sh" && conda activate py311 && module load singularity && export PATH="/mnt/projects/CCBR-Pipelines/bin:$PATH"'
    )
