import json
import os
import sys


def get_singularity_cachedir(output_dir, cache_dir=None):
    """Returns the singularity cache directory.
    If no user-provided cache directory is provided,
    the default singularity cache is in the output directory.
    """
    if not cache_dir:
        cache_dir = os.path.join(output_dir, ".singularity")
    return cache_dir


def get_sif_cache_dir(hpc=None):
    sif_dir = None
    if hpc == "biowulf":
        sif_dir = "/data/CCBR_Pipeliner/SIFS"
    elif hpc == "frce":
        sif_dir = "/mnt/projects/CCBR-Pipelines/SIFs"
    return sif_dir


def image_cache(sub_args, config):
    """Adds Docker Image URIs, or SIF paths to config if singularity cache option is provided.
    If singularity cache option is provided and a local SIF does not exist, a warning is
    displayed and the image will be pulled from URI in 'config/containers/images.json'.
    @param sub_args <parser.parse_args() object>:
        Parsed arguments for run sub-command
    @params config <file>:
        Docker Image config file
    @return config <dict>:
         Updated config dictionary containing user information (username and home directory)
    """
    images = os.path.join(sub_args.output, "config", "containers", "images.json")

    # Read in config for docker image uris
    with open(images, "r") as fh:
        data = json.load(fh)
    # Check if local sif exists
    for image, uri in data["images"].items():
        if sub_args.sif_cache:
            sif = os.path.join(
                sub_args.sif_cache,
                "{}.sif".format(os.path.basename(uri).replace(":", "_")),
            )
            if not os.path.exists(sif):
                # If local sif does not exist on in cache, print warning
                # and default to pulling from URI in config/containers/images.json
                print(
                    'Warning: Local image "{}" does not exist in singularity cache'.format(
                        sif
                    ),
                    file=sys.stderr,
                )
            else:
                # Change pointer to image from Registry URI to local SIF
                data["images"][image] = sif

    config.update(data)

    return config
