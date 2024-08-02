import datetime
import glob
import os
import subprocess
import shutil
import sys
import warnings


def renee_base(rel_path=""):
    """Get the absolute path to a file in the RENEE repository
    @return abs_path <str>
    """
    basedir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    )
    return os.path.join(basedir, rel_path)


def get_version():
    """Get the current RENEE version
    @return version <str>
    """
    with open(renee_base("VERSION"), "r") as vfile:
        version = f"v{vfile.read().strip()}"
    return version


def scontrol_show():
    """Run scontrol show config and parse the output as a dictionary
    @return scontrol_dict <dict>:
    """
    scontrol_dict = dict()
    scontrol_out = subprocess.run(
        "scontrol show config", shell=True, capture_output=True, text=True
    ).stdout
    if len(scontrol_out) > 0:
        for line in scontrol_out.split("\n"):
            line_split = line.split("=")
            if len(line_split) > 1:
                scontrol_dict[line_split[0].strip()] = line_split[1].strip()
    return scontrol_dict


def get_hpcname():
    """Get the HPC name (biowulf, frce, or an empty string)
    @return hpcname <str>
    """
    scontrol_out = scontrol_show()
    hpc = scontrol_out["ClusterName"] if "ClusterName" in scontrol_out.keys() else ""
    if hpc == "fnlcr":
        hpc = "frce"
    return hpc


def get_tmp_dir(tmp_dir, outdir, hpc=get_hpcname()):
    """Get default temporary directory for biowulf and frce. Allow user override."""
    if not tmp_dir:
        if hpc == "biowulf":
            tmp_dir = "/lscratch/$SLURM_JOBID"
        elif hpc == "frce":
            tmp_dir = outdir
        else:
            tmp_dir = None
    return tmp_dir


def get_shared_resources_dir(shared_dir, outdir, hpc=get_hpcname()):
    """Get default shared resources directory for biowulf and frce. Allow user override."""
    if not shared_dir:
        if hpc == "biowulf":
            shared_dir = (
                "/data/CCBR_Pipeliner/Pipelines/RENEE/resources/shared_resources"
            )
        elif hpc == "frce":
            shared_dir = "/mnt/projects/CCBR-Pipelines/pipelines/RENEE/resources/shared_resources"
    return shared_dir


def get_genomes_list(
    hpcname=get_hpcname(),
):  # TODO call get_genomes_dict and extract list; only warn if no genomes found
    """Get list of genome annotations available for the current platform
    @return genomes_list <list>
    """
    genome_config_dir = renee_base(os.path.join("config", "genomes", hpcname))
    json_files = glob.glob(genome_config_dir + "/*.json")
    if not json_files:
        warnings.warn(
            f"WARNING: No Genome Annotation JSONs found in {genome_config_dir}. Please specify a custom genome json file with `--genome`"
        )
    genomes = [os.path.basename(file).replace(".json", "") for file in json_files]
    return sorted(genomes)


def get_genomes_dict(
    hpcname=get_hpcname(),
):  # TODO option to either warn or error if genomes not found
    """Get dictionary of genome annotation versions and the paths to the corresponding JSON files
    @return genomes_dict <dict> { genome_name: json_file_path }
    """
    genomes_dir = renee_base(os.path.join("config", "genomes", hpcname))
    if not os.path.exists(genomes_dir):
        raise FileNotFoundError(f"ERROR: Folder does not exist : {genomes_dir}")
    search_term = genomes_dir + "/*.json"
    json_files = glob.glob(search_term)
    if len(json_files) == 0:
        raise FileNotFoundError(
            f"ERROR: No Genome+Annotation JSONs found in : {genomes_dir}"
        )
    genomes_dict = {
        os.path.basename(json_file).replace(".json", ""): json_file
        for json_file in json_files
    }
    return genomes_dict


def check_python_version():
    # version check
    # glob.iglob requires 3.11 for using "include_hidden=True"
    MIN_PYTHON = (3, 11)
    try:
        assert sys.version_info >= MIN_PYTHON
        print(
            "Python version: {0}.{1}.{2}".format(
                sys.version_info.major, sys.version_info.minor, sys.version_info.micro
            )
        )
    except AssertionError:
        exit(
            f"{sys.argv[0]} requires Python {'.'.join([str(n) for n in MIN_PYTHON])} or newer"
        )


def _cp_r_safe_(
    source, target, resources=["workflow", "resources", "config"], safe_mode=True
):
    """Private function: Given a list paths it will recursively copy each to the
    target location. If a target path already exists, it will not over-write the
    existing paths data when `safe_mode` is on.
    @param resources <list[str]>:
        List of paths to copy over to target location.
        Default: ["workflow", "resources", "config"]
    @params source <str>:
        Add a prefix PATH to each resource
    @param target <str>:
        Target path to copy templates and required resources (aka destination)
    @param safe_mode <bool>:
        Only copy the resources to the target path
        if they do not exist in the target path (default: True)
    """
    for resource in resources:
        destination = os.path.join(target, resource)
        if os.path.exists(destination) and safe_mode:
            print(f"🚫 path exists and `safe_mode` is ON, not copying: {destination}")
        else:
            # Required resources do not exist, or safe mode is off
            shutil.copytree(
                os.path.join(source, resource), destination, dirs_exist_ok=not safe_mode
            )


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
    hpcname="",
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
    cache = os.path.join(outdir, ".singularity")
    my_env["SINGULARITY_CACHEDIR"] = cache

    if alt_cache:
        # Override the pipeline's default cache location
        my_env["SINGULARITY_CACHEDIR"] = alt_cache
        cache = alt_cache

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

    return masterjob


def _get_file_mtime(f):
    timestamp = datetime.fromtimestamp(os.path.getmtime(os.path.abspath(f)))
    mtime = timestamp.strftime("%y%m%d%H%M%S")
    return mtime
