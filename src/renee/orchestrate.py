import os
import subprocess

from ccbr_tools.pipeline.util import (
    get_hpcname,
    get_tmp_dir,
)
from ccbr_tools.pipeline.cache import get_singularity_cachedir


def orchestrate(
    mode,
    outdir,
    additional_bind_paths,
    alt_cache,
    threads=2,
    submission_script="runner",
    masterjob="pl:renee",
    tmp_dir=None,
    wait="",
    hpcname=get_hpcname(),
):
    """Runs RENEE pipeline via selected executor: local or slurm.
    If 'local' is selected, the pipeline is executed locally on a compute node/instance.
    If 'slurm' is selected, jobs will be submitted to the cluster using SLURM job scheduler.
    Support for additional job schedulers (i.e. PBS, SGE, LSF) may be added in the future.
    @param outdir <str>:
        Pipeline output PATH
    @param mode <str>:
        Execution method or mode:
            local runs serially a compute instance without submitting to the cluster.
            slurm will submit jobs to the cluster using the SLURM job scheduler.
    @param additional_bind_paths <str>:
        Additional paths to bind to container filesystem (i.e. input file paths)
    @param alt_cache <str>:
        Alternative singularity cache location
    @param threads <str>:
        Number of threads to use for local execution method
    @param submission_script <str>:
        Path to master jobs submission script:
            renee run =   /path/to/output/resources/runner
            renee build = /path/to/output/resources/builder
    @param masterjob <str>:
        Name of the master job
    @param tmp_dir <str>:
        Absolute Path to temp dir for compute node
    @param wait <str>:
        "--wait" to wait for master job to finish. This waits when pipeline is called via NIDAP API
    @param hpcname <str>:
        "biowulf" if run on biowulf, "frce" if run on frce, blank otherwise. hpcname is determined in setup() function
    @return masterjob <subprocess.Popen() object>:
    """
    # Add additional singularity bind PATHs
    # to mount the local filesystem to the
    # containers filesystem, NOTE: these
    # PATHs must be an absolute PATHs
    outdir = os.path.abspath(outdir)
    # Add any default PATHs to bind to
    # the container's filesystem, like
    # tmp directories, /lscratch
    addpaths = []
    # set tmp_dir depending on hpc
    tmp_dir = get_tmp_dir(tmp_dir, outdir)
    temp = os.path.dirname(tmp_dir.rstrip("/"))
    if temp == os.sep:
        temp = tmp_dir.rstrip("/")
    if outdir not in additional_bind_paths.split(","):
        addpaths.append(outdir)
    if temp not in additional_bind_paths.split(","):
        addpaths.append(temp)
    bindpaths = ",".join(addpaths)

    # Set ENV variable 'SINGULARITY_CACHEDIR'
    # to output directory
    my_env = {}
    my_env.update(os.environ)

    cache = get_singularity_cachedir(output_dir=outdir, cache_dir=alt_cache)
    my_env["SINGULARITY_CACHEDIR"] = cache

    if additional_bind_paths:
        # Add Bind PATHs for outdir and tmp dir
        if bindpaths:
            bindpaths = ",{}".format(bindpaths)
        bindpaths = "{}{}".format(additional_bind_paths, bindpaths)

    if not os.path.exists(os.path.join(outdir, "logfiles")):
        # Create directory for logfiles
        os.makedirs(os.path.join(outdir, "logfiles"))

    if os.path.exists(os.path.join(outdir, "logfiles", "snakemake.log")):
        mtime = _get_file_mtime(os.path.join(outdir, "logfiles", "snakemake.log"))
        newname = os.path.join(outdir, "logfiles", "snakemake." + str(mtime) + ".log")
        os.rename(os.path.join(outdir, "logfiles", "snakemake.log"), newname)

    # Create .singularity directory for installations of snakemake
    # without setuid which create a sandbox in the SINGULARITY_CACHEDIR
    if not os.path.exists(cache):
        # Create directory for sandbox and image layers
        os.makedirs(cache)

    # Run on compute node or instance without submitting jobs to a scheduler
    if mode == "local":
        # Run RENEE: instantiate main/master process
        # Look into later: it maybe worth replacing Popen subprocess with a direct
        # snakemake API call: https://snakemake.readthedocs.io/en/stable/api_reference/snakemake.html
        # Create log file for pipeline
        logfh = open(os.path.join(outdir, "logfiles", "snakemake.log"), "w")
        masterjob = subprocess.Popen(
            [
                "snakemake",
                "-pr",
                "--use-singularity",
                "--singularity-args",
                "'-B {}'".format(bindpaths),
                "--cores",
                str(threads),
                "--configfile=config.json",
            ],
            cwd=outdir,
            env=my_env,
        )

    # Submitting jobs to cluster via SLURM's job scheduler
    elif mode == "slurm":
        # Run RENEE: instantiate main/master process
        # Look into later: it maybe worth replacing Popen subprocess with a direct
        # snakemake API call: https://snakemake.readthedocs.io/en/stable/api_reference/snakemake.html
        # snakemake --latency-wait 120  -s $R/Snakefile -d $R --printshellcmds
        #    --cluster-config $R/cluster.json --keep-going --restart-times 3
        #    --cluster "sbatch --gres {cluster.gres} --cpus-per-task {cluster.threads} -p {cluster.partition} -t {cluster.time} --mem {cluster.mem} --job-name={params.rname}"
        #    -j 500 --rerun-incomplete --stats $R/Reports/initialqc.stats -T
        #    2>&1| tee -a $R/Reports/snakemake.log

        # Create log file for master job information
        logfh = open(os.path.join(outdir, "logfiles", "master.log"), "w")
        # submission_script for renee run is /path/to/output/resources/runner
        # submission_script for renee build is /path/to/output/resources/builder
        cmdlist = [
            str(os.path.join(outdir, "resources", str(submission_script))),
            mode,
            "-j",
            str(masterjob),
            "-b",
            str(bindpaths),
            "-o",
            str(outdir),
            "-c",
            str(cache),
            "-t",
            str(tmp_dir),
        ]
        if str(wait) == "--wait":
            cmdlist.append("-w")
        if str(hpcname) != "":
            cmdlist.append("-n")
            cmdlist.append(hpcname)
        else:
            cmdlist.append("-n")
            cmdlist.append("unknown")

        print(" ".join(cmdlist))
        masterjob = subprocess.Popen(
            cmdlist, cwd=outdir, stderr=subprocess.STDOUT, stdout=logfh, env=my_env
        )
    logfh.close()
    return masterjob
