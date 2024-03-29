# <code>renee <b>cache</b></code>

## 1. About

The `renee` executable is composed of several inter-related sub commands. Please see `renee -h` for all available options.

This part of the documentation describes options and concepts for <code>renee <b>cache</b></code> sub command in more detail. With minimal configuration, the **`cache`** sub command enables you to cache remote resources for the RENEE pipeline. Caching remote resources allows the pipeline to run in an offline mode.

`renee cache` when run successfully submits a SLURM job to the job schedule and quits. `squeue` can then be used to track the progress of the caching.

The cache sub command creates local cache on the filesysytem for resources hosted on DockerHub or AWS S3. These resources are normally pulled onto the filesystem when the pipeline runs; however, due to network issues or DockerHub pull rate limits, it may make sense to pull the resources once so a shared cache can be created and re-used. It is worth noting that a singularity cache cannot normally be shared across users. Singularity strictly enforces that its cache is owned by the user. To get around this issue, the cache subcommand can be used to create local SIFs on the filesystem from images on DockerHub.

Caching remote resources for the RENEE pipeline is fast and easy! In its most basic form, <code>renee <b>cache</b></code> only has _one required input_.

## 2. Synopsis

```text
$ renee cache [-h] --sif-cache SIF_CACHE \
                        [--dry-run]
```

The synopsis for each command shows its parameters and their usage. Optional parameters are shown in square brackets.

A user **must** provide a directory to cache remote Docker images via the `--sif-cache` argument. Once the cache has pipeline completed, the local sif cache can be passed to the `--sif-cache` option of the <code>renee <b>build</b></code> and <code>renee <b>run</b></code> subcomand. This enables the build and run pipeline to run in an offline mode.

Use you can always use the `-h` option for information on a specific command.

### 2.1 Required Arguments

`--sif-cache SIF_CACHE`

> **Path where a local cache of SIFs will be stored.**  
> _type: path_
>
> Any images defined in _config/containers/images.json_ will be pulled into the local filesystem. The path provided to this option can be passed to the `--sif-cache` option of the <code>renee <b>build</b></code> and <code>renee <b>run</b></code> subcomand. This allows for running the build and run pipelines in an offline mode where no requests are made to external sources. This is useful for avoiding network issues or DockerHub pull rate limits. Please see renee build and run for more information.
>
> **_Example:_** `--sif-cache /data/$USER/cache`

### 2.2 Options

Each of the following arguments are optional and do not need to be provided.

`-h, --help`

> **Display Help.**  
> _type: boolean_
>
> Shows command's synopsis, help message, and an example command
>
> **_Example:_** `--help`

---

`--dry-run`

> **Dry run the pipeline.**  
> _type: boolean_
>
> Displays what steps in the pipeline remain or will be run. Does not execute anything!
>
> **_Example:_** `--dry-run`

## 3. Example

```bash
# Step 0.) Grab an interactive node (do not run on head node)
srun -N 1 -n 1 --time=12:00:00 -p interactive --mem=8gb  --cpus-per-task=4 --pty bash
module purge
module load ccbrpipeliner

# Step 1.) Dry run cache to see what will be pulled
renee cache --sif-cache /data/$USER/cache \
                 --dry-run

# Step 2.) Cache remote resources locally
renee cache --sif-cache /data/$USER/cache
```
