#!/usr/bin/env python3


global DEBUG

DEBUG = True

import glob
import os
import PySimpleGUI as sg
import sys
import stat
import subprocess
from tkinter import Tk
import uuid


# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)

# adding the parent directory to
# the sys.path.
sys.path.append(parent)
imgdir = os.path.join(parent, "resources", "images")

global RENEEDIR
global SIFCACHE
global RENEE
global RENEEVER
global RANDOMSTR
global FILES2DELETE
global HOSTNAME

RENEEDIR = os.getenv("RENEEDIR")
SIFCACHE = os.getenv("SIFCACHE")
RENEEVER = os.getenv("RENEEVER")
HOSTNAME = os.getenv("HOSTNAME")
RENNE = os.path.join(RENEEDIR, RENEEVER, "bin", "renee")
RANDOMSTR = str(uuid.uuid4())
FILES2DELETE = list()

# sg.SetOptions(button_color=sg.COLOR_SYSTEM_DEFAULT)


def version_check():
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


def copy_to_clipboard(string):
    r = Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(string)
    r.update()
    r.destroy()


def get_combos():
    resource_dir = os.path.join(RENEEDIR, "resources")
    if not os.path.exists(resource_dir):
        sys.exit("ERROR: Folder does not exist : {}".format(resource_dir))
    searchterm = resource_dir + "/**/**/*json"
    jsonfiles = glob.glob(searchterm)
    if len(jsonfiles) == 0:
        sys.exit("ERROR: No Genome+Annotation JSONs found in : {}".format(resource_dir))
    jsons = dict()
    for j in jsonfiles:
        k = os.path.basename(j)
        k = k.replace(".json", "")
        jsons[k] = j
    return jsons


def fixpath(p):
    return os.path.abspath(os.path.expanduser(p))


def get_fastqs(inputdir):
    inputdir = fixpath(inputdir)
    inputfastqs = glob.glob(inputdir + os.sep + "*.fastq.gz")
    inputfqs = glob.glob(inputdir + os.sep + "*.fq.gz")
    inputfastqs.extend(inputfqs)
    return inputfastqs


def deletefiles():
    for f in FILES2DELETE:
        if os.path.exists(f):
            os.remove(f)


def run(cmd, dry=False):
    if dry:
        cmd += " --dry-run "
    runner_file = os.path.join(os.getenv("HOME"), RANDOMSTR + ".renee.runner")
    FILES2DELETE.append(runner_file)
    with open(runner_file, "w") as runner:
        runner.write(cmd)
    st = os.stat(runner_file)
    os.chmod(runner_file, st.st_mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    x = subprocess.run(runner_file, capture_output=True, shell=True, text=True)
    run_stdout = x.stdout.encode().decode("utf-8")
    run_stderr = x.stderr.encode().decode("utf-8")
    return run_stdout, run_stderr


def main():
    # get drop down genome+annotation options
    jsons = get_combos()
    genome_annotation_combinations = list(jsons.keys())
    genome_annotation_combinations.sort()
    if DEBUG:
        print(jsons)
    if DEBUG:
        print(genome_annotation_combinations)

    logo = sg.Image(os.path.join(imgdir, "CCBRlogo.png"))
    # create layout
    layout = [
        [sg.Column([[logo]], justification="center")],
        [
            sg.Text(
                "RENEE - Rna sEquencing aNalysis pipElinE", font=("Arial", 14, "bold")
            )
        ],
        [
            sg.Text(
                "Input Fastqs folder", font=("Helvetica", 12, "bold"), size=(20, 1)
            ),
            sg.InputText(key="--INDIR--"),
            sg.FolderBrowse(target="--INDIR--"),
        ],
        [
            sg.Text("Output folder", font=("Helvetica", 12, "bold"), size=(20, 1)),
            sg.InputText(key="--OUTDIR--"),
            sg.FolderBrowse(target="--OUTDIR--"),
        ],
        [
            sg.Text("Genome+Annotation", font=("Helvetica", 12, "bold"), size=(20, 1)),
            sg.Combo(
                values=genome_annotation_combinations,
                key="--ANNOTATION--",
                tooltip="eg. hg38_30 for Genome=hg38 & Gencode_Annotation=version 30",
            ),
        ],
        [
            sg.Submit(key="--SUBMIT--", font=("Helvetica", 12)),
            sg.Cancel(key="--CANCEL--", font=("Helvetica", 12)),
            sg.Button(
                button_text="Documentation", key="--DOC--", font=("Helvetica", 12)
            ),
            sg.Button(button_text="Help", key="--HELP--", font=("Helvetica", 12)),
        ],
    ]
    if DEBUG:
        print("layout is ready!")

    window = sg.Window("RENEE " + RENEEVER, layout, location=(0, 500), finalize=True)
    if DEBUG:
        print("window created!")

    while True:
        event, values = window.read()
        if DEBUG:
            print(event, values)
        # if any((event != 'Submit')):
        if event == "--CANCEL--" or event == sg.WIN_CLOSED:
            sg.popup_auto_close(
                "Thank you for running RENEE. GoodBye!",
                location=(0, 500),
                title="",
                font=("Arial", 12, "bold"),
            )
            sys.exit(69)
        if event == "--DOC--":
            copy_to_clipboard("https://ccbr.github.io/RENEE/")
            sg.Popup(
                "Visit https://ccbr.github.io/RENEE/ for links to complete documentation. The link has been copied to your clipboard. Please paste it in your favorite web browser.",
                font=("Arial", 12, "bold"),
                location=(0, 500),
            )
            continue
        if event == "--HELP--":
            copy_to_clipboard("ccbr_pipeliner@mail.nih.gov")
            sg.Popup(
                "Email ccbr_pipeliner@mail.nih.gov for help. The email id has been copied to your clipboard. Please paste it in your emailing software.",
                font=("Arial", 12, "bold"),
                location=(0, 500),
            )
            continue
        if event == "--SUBMIT--":
            if values["--INDIR--"] == "":
                sg.PopupError(
                    "Input folder must be provided!!",
                    location=(0, 500),
                    title="ERROR!",
                    font=("Arial", 12, "bold"),
                )
                continue
            elif not os.path.exists(values["--INDIR--"]) and not os.path.exists(
                fixpath(values["--INDIR--"])
            ):
                if DEBUG:
                    print(values["--INDIR--"])
                if DEBUG:
                    print(fixpath(values["--INDIR--"]))
                sg.PopupError(
                    "Input folder doesnt exist!!",
                    location=(0, 500),
                    title="ERROR!",
                    font=("Arial", 12, "bold"),
                )
                continue
            else:
                inputfastqs = get_fastqs(values["--INDIR--"])
                if DEBUG:
                    print(inputfastqs)
                if len(inputfastqs) == 0:
                    sg.PopupError(
                        "Input folder has no fastqs!!",
                        location=(0, 500),
                        title="ERROR!",
                        font=("Arial", 12, "bold"),
                    )
                    window.Element("--INDIR--").update("")
                    continue
            if values["--OUTDIR--"] == "":
                sg.PopupError(
                    "Output folder must be provided!!",
                    location=(0, 500),
                    title="ERROR",
                    font=("Arial", 12, "bold"),
                )
                continue
            elif os.path.exists(values["--OUTDIR--"]) and not os.path.exists(
                fixpath(values["--OUTDIR--"])
            ):
                ch = sg.popup_yes_no(
                    "Output folder exists... this is probably a re-run ... proceed?",
                    title="Rerun?",
                    location=(0, 500),
                    font=("Arial", 12, "bold"),
                )
                if ch == "No":
                    window.Element("--OUTDIR--").update("")
                    continue
                # sg.Popup("Output folder exists... this is probably a re-run ... is it?",location=(0,500))
            genome = jsons[values["--ANNOTATION--"]]
            renee_cmd = RENNE + " run "
            renee_cmd += " --input " + " ".join(inputfastqs)
            renee_cmd += " --output " + values["--OUTDIR--"]
            renee_cmd += " --genome " + genome
            renee_cmd += " --sif-cache " + SIFCACHE
            renee_cmd += " --mode slurm "
            # if HOSTNAME != "biowulf.nih.gov":
            if HOSTNAME == "fsitgl-head01p.ncifcrf.gov":
                renee_cmd += " --tmp-dir /scratch/cluster_scratch/$USER "
                renee_cmd += " --shared-resources /mnt/projects/CCBR-Pipelines/pipelines/RENEE/resources/shared_resources "
            run_stdout, run_stderr = run(renee_cmd, dry=True)
            if DEBUG:
                print(run_stdout)
            if DEBUG:
                print(run_stderr)
            allout = "{}\n{}".format(run_stdout, run_stderr)
            sg.popup_scrolled(
                allout,
                title="Dryrun:STDOUT/STDERR",
                font=("Monaco", 10),
                location=(0, 500),
                size=(80, 30),
            )
            if "error" in allout or "Error" in allout or "ERROR" in allout:
                continue
            ch = sg.popup_yes_no(
                "Submit run to slurm?",
                title="Submit??",
                location=(0, 500),
                font=("Arial", 12, "bold"),
            )
            if ch == "Yes":
                run_stdout, run_stderr = run(renee_cmd, dry=False)
                if DEBUG:
                    print(run_stdout)
                if DEBUG:
                    print(run_stderr)
                allout = "{}\n{}".format(run_stdout, run_stderr)
                sg.popup_scrolled(
                    allout,
                    title="Slurmrun:STDOUT/STDERR",
                    font=("Monaco", 10),
                    location=(0, 500),
                    size=(80, 30),
                )
                sg.popup_auto_close(
                    "Thank you for running RENEE. GoodBye!",
                    location=(0, 500),
                    title="",
                    font=("Arial", 12, "bold"),
                )
                break
            elif ch == "No":
                window.Element("--INDIR--").update("")
                window.Element("--OUTDIR--").update("")
                window.Element("--ANNOTATION--").update("")
                continue

    window.close()
    if len(FILES2DELETE) != 0:
        deletefiles()


# ./renee run \
#   --input ../.tests/*.R?.fastq.gz \
#   --output /data/${USER}/RENEE_testing_230703/RNA_hg38 \
#   --genome /data/CCBR_Pipeliner/Pipelines/RENEE/resources/hg38/30/hg38_30.json \
#   --sif-cache /data/CCBR_Pipeliner/SIFS/ \
#   --mode slurm

if __name__ == "__main__":
    version_check()
    main()
