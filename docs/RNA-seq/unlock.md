# <code>renee <b>unlock</b></code>

## 1. About

The `renee` executable is composed of several inter-related sub commands. Please see `renee -h` for all available options.

This part of the documentation describes options and concepts for <code>renee <b>unlock</b></code> sub command in more detail. With minimal configuration, the **`unlock`** sub command enables you to unlock a pipeline output directory.

If the pipeline fails ungracefully, it maybe required to unlock the working directory before proceeding again. Snakemake will inform a user when it maybe necessary to unlock a working directory with an error message stating: `Error: Directory cannot be locked`.

Please verify that the pipeline is not running before running this command. If the pipeline is currently running, the workflow manager will report the working directory is locked. The is the default behavior of snakemake, and it is normal. Do NOT run this command if the pipeline is still running! Please kill the master job and it's child jobs prior to running this command.

Unlocking an RENEE pipeline output directory is fast and easy! In its most basic form, <code>renee <b>run</b></code> only has _one required inputs_.

## 2. Synopsis

```text
$ renee unlock [-h] --output OUTPUT
```

The synopsis for this command shows its parameters and their usage. Optional parameters are shown in square brackets.

A user **must** provide an output directory to unlock via `--output` argument. After running the unlock sub command, you can resume the build or run pipeline from where it left off by re-running it.

Use you can always use the `-h` option for information on a specific command.

### 2.1 Required Arguments

`--output OUTPUT`

> **Output directory to unlock.**  
> _type: path_
>
> Path to a previous run's output directory to unlock. This will remove a lock on the working directory. Please verify that the pipeline is not running before running this command.  
> **_Example:_** `--output /data/$USER/RNA_hg38`

### 2.2 Options

Each of the following arguments are optional and do not need to be provided.

`-h, --help`

> **Display Help.**  
> _type: boolean_
>
> Shows command's synopsis, help message, and an example command
>
> **_Example:_** `--help`

## 3. Example

```bash
# Step 0.) Grab an interactive node (do not run on head node)
srun -N 1 -n 1 --time=12:00:00 -p interactive --mem=8gb  --cpus-per-task=4 --pty bash
module purge
module load ccbrpipeliner

# Step 1.) Unlock a pipeline output directory
renee unlock --output /data/$USER/RNA_hg38
```
