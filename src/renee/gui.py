#!/usr/bin/env python3
import argparse
import glob
import io
import os
import PySimpleGUI as sg
import sys
from tkinter import Tk

from .util import (
    get_genomes_dict,
    get_tmp_dir,
    get_shared_resources_dir,
    renee_base,
    get_version,
)
from .cache import get_sif_cache_dir
from .run import run_in_context

# TODO: get rid of  all the global variables
# TODO: let's use a tmp dir and put these files there instead. see for inspiration:https://github.com/CCBR/RENEE/blob/16d13dca1d5f0f43c7dfda379efb882a67635d17/tests/test_cache.py#L14-L28
global FILES_TO_DELETE
FILES_TO_DELETE = list()


def launch_gui(sub_args, debug=True):
    # get drop down genome+annotation options
    jsons = get_genomes_dict(error_on_warnings=True)
    genome_annotation_combinations = list(jsons.keys())
    genome_annotation_combinations.sort()
    if debug:
        print(jsons)
    if debug:
        print(genome_annotation_combinations)

    logo = sg.Image(renee_base(os.path.join("resources", "CCBRlogo.png")))
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
    if debug:
        print("layout is ready!")

    window = sg.Window(
        f"RENEE {get_version()}", layout, location=(0, 500), finalize=True
    )
    if debug:
        print("window created!")

    while True:
        event, values = window.read()
        if debug:
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
                if debug:
                    print(values["--INDIR--"])
                if debug:
                    print(fixpath(values["--INDIR--"]))
                sg.PopupError(
                    "Input folder doesn't exist!!",
                    location=(0, 500),
                    title="ERROR!",
                    font=("Arial", 12, "bold"),
                )
                continue
            else:
                inputfastqs = get_fastqs(values["--INDIR--"])
                if debug:
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
            output_dir = values["--OUTDIR--"]
            # create sub args for renee run
            run_args = argparse.Namespace(
                input=inputfastqs,
                output=output_dir,
                genome=genome,
                mode="slurm",
                runmode="run",
                dry_run=True,
                sif_cache=get_sif_cache_dir(),
                singularity_cache=os.environ["SINGULARITY_CACHEDIR"],
                tmp_dir=get_tmp_dir("", output_dir),
                shared_resources=get_shared_resources_dir("", output_dir),
                star_2_pass_basic=False,
                small_rna=False,
                create_nidap_folder=False,
                wait=False,
                threads=2,
            )
            # execute dry run and capture stdout/stderr
            allout = run_in_context(run_args)
            sg.popup_scrolled(
                allout,
                title="Dryrun:STDOUT/STDERR",
                font=("Monaco", 10),
                location=(0, 500),
                size=(80, 30),
            )
            # TODO use a regex to simplify this line
            if "error" in allout or "Error" in allout or "ERROR" in allout:
                continue
            ch = sg.popup_yes_no(
                "Submit run to slurm?",
                title="Submit??",
                location=(0, 500),
                font=("Arial", 12, "bold"),
            )
            if ch == "Yes":
                run_args.dry_run = False
                # execute live run
                allout = run_in_context(run_args)
                sg.popup_scrolled(
                    allout,
                    title="Dryrun:STDOUT/STDERR",
                    font=("Monaco", 10),
                    location=(0, 500),
                    size=(80, 30),
                )
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
    if len(FILES_TO_DELETE) != 0:
        delete_files(FILES_TO_DELETE)


def copy_to_clipboard(string):
    r = Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(string)
    r.update()
    r.destroy()


def fixpath(p):
    return os.path.abspath(os.path.expanduser(p))


def get_fastqs(inputdir):
    inputdir = fixpath(inputdir)
    inputfastqs = glob.glob(inputdir + os.sep + "*.fastq.gz")
    inputfqs = glob.glob(inputdir + os.sep + "*.fq.gz")
    inputfastqs.extend(inputfqs)
    return inputfastqs


def delete_files(files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)


if __name__ == "__main__":
    launch_gui()
