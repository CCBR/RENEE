#!/usr/bin/env python3
import json
import os
import pathlib
import sys


def main(args):
    for fp in args:
        with open(fp, "r") as file:
            conf_dict = json.load(file)
            for conf_value in conf_dict["references"]["rnaseq"].values():
                if isinstance(conf_value, str) and conf_value.startswith("/"):
                    check_path(conf_value)


def check_path(fp, repair=False):
    path = pathlib.Path(fp)
    if path.is_symlink():
        target = path.resolve()
        if (
            str(target).startswith("/gpfs") or not target.exists()
        ):  # PermissionError: [Errno 13] Permission denied: '/gpfs/gsfs10/users/CCBR_Pipeliner/db/PipeDB/GDC_refs/downloads/GRCh37.p13.genome.d1.vd1.genome.fa'
            print(f"Broken symlink: {path} -> {target}")
            target_new = str(target).replace(
                "/gpfs/gsfs10/users/CCBR_Pipeliner/", "/data/CCBR_Pipeliner/"
            )
            assert pathlib.Path(
                target_new
            ).exists(), f"\tNew target path does not exist: {target_new}"
            if repair:
                path.unlink()
                path.symlink_to(target_new)
                print(f"\tRepaired symlink: {path} -> {target_new}")
            else:
                print(f"\tnew symlink should point to -> {target_new}")
        else:
            print(f"Valid symlink: {path} -> {target}")
    # else:
    #     print(f"Not a symlink: {path}")


if __name__ == "__main__":
    main(sys.argv[1:])
