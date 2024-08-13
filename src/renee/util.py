import pathlib
from ccbr_tools.pipeline.util import get_hpcname


def renee_base(*paths):
    """Get the absolute path to a file in the repository
    @return abs_path <str>
    """
    basedir = pathlib.Path(__file__).absolute().parent.parent.parent
    return basedir.joinpath(*paths)


def get_version():
    """Get the current RENEE version
    @return version <str>
    """
    with open(renee_base("VERSION"), "r") as vfile:
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
