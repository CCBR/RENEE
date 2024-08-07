import datetime
import os
import subprocess
import sys


def dryrun(
    outdir,
    config="config.json",
    snakefile=os.path.join("workflow", "Snakefile"),
    write_to_file=True,
):
    """Dryruns the pipeline to ensure there are no errors prior to running.
    @param outdir <str>:
        Pipeline output PATH
    @return dryrun_output <str>:
        Byte string representation of dryrun command
    """
    try:
        dryrun_output = subprocess.check_output(
            [
                "snakemake",
                "-npr",
                "-s",
                str(snakefile),
                "--use-singularity",
                "--rerun-incomplete",
                "--cores",
                "4",
                "--configfile={}".format(config),
            ],
            cwd=outdir,
            stderr=subprocess.STDOUT,
        )

    except subprocess.CalledProcessError as e:
        # Singularity is NOT in $PATH
        # Tell user to load both main dependencies to avoid the OSError below
        print(
            "Are singularity and snakemake in your PATH? Please check before proceeding again!"
        )
        sys.exit("{}\n{}".format(e, e.output.decode("utf-8")))
    except OSError as e:
        # Catch: OSError: [Errno 2] No such file or directory
        #  Occurs when command returns a non-zero exit-code
        if e.errno == 2 and not exe_in_path("snakemake"):
            # Failure caused because snakemake is NOT in $PATH
            print(
                "\x1b[6;37;41m\nError: Are snakemake AND singularity in your $PATH?\nPlease check before proceeding again!\x1b[0m",
                file=sys.stderr,
            )
            sys.exit("{}".format(e))
        else:
            # Failure caused by unknown cause, raise error
            raise e

    if write_to_file:
        now = _now()
        with open(os.path.join(outdir, "dryrun." + str(now) + ".log"), "w") as outfile:
            outfile.write("{}".format(dryrun_output.decode("utf-8")))

    return dryrun_output


def _now():
    ct = datetime.datetime.now()
    now = ct.strftime("%y%m%d%H%M%S")
    return now


def exe_in_path(cmd, path=None):
    """Checks if an executable is in $PATH
    @param cmd <str>:
        Name of executable to check
    @param path <list>:
        Optional list of PATHs to check [default: $PATH]
    @return <boolean>:
        True if exe in PATH, False if not in PATH
    """
    if path is None:
        path = os.environ["PATH"].split(os.pathsep)

    for prefix in path:
        filename = os.path.join(prefix, cmd)
        executable = os.access(filename, os.X_OK)
        is_not_directory = os.path.isfile(filename)
        if executable and is_not_directory:
            return True
    return False
