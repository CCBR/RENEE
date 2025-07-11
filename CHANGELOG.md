## RENEE development version

## RENEE 2.7.1

- Improvements for fastq validator: (#224, @kelly-sovacool)
  - Increase default memory.
  - Capture stdout in a log file so the output is not deleted on failure.
- Fix broken symlinks for genome reference files on biowulf. (#226, @kelly-sovacool)

## RENEE 2.7.0

- RENEE now depends on ccbr_tools v0.4 for updated jobby & spooker utilities. (#207, @kelly-sovacool)
- Add `mmul10_108` (rhesus macaque) to list of reference genomes. (#212, @kelly-sovacool)
- Added support for new reference genomes on biowulf:
  - `mm39_M36` (#199, @kelly-sovacool)
  - `mm39_M37` (#220, @kelly-sovacool)
  - `hg38_48` (#220, @kelly-sovacool)
- Fix `--sif-cache` example in docs. (#208, @kelly-sovacool)

## RENEE 2.6.8

- Fix broken symlinks for genome reference files on biowulf. (#226, @kelly-sovacool)

## RENEE 2.6.7

- Minor CLI fixes. (#202, #203, @kelly-sovacool)

## RENEE 2.6.6

- Minor documentation updates. (#198, @kelly-sovacool)

## RENEE 2.6.5

- Critical bug fix: use local copies of Arriba resources for biowulf & frce instead of downloading them from an S3 bucket. (#191, @kelly-sovacool)
- Increase memory for `fastq_screen`. (#188, @kelly-sovacool)

## RENEE 2.6.4

- Fix spelling of shared SIF directory on biowulf -- it is `/data/CCBR_Pipeliner/SIFs` with a lowercase "s" at the end. (#182, @kelly-sovacool)
- Raise an error if too few reads are left after trimming with cutadapt. (#184, @kelly-sovacool)
- Reformat GTF files during `renee build` that are missing 'gene_biotype' or 'gene_type' attributes in exons. (#185, @kelly-sovacool)
- Add support for the marmoset genome (mCalJac1 2021). (#185, @kelly-sovacool)

## RENEE 2.6.3

- Upgrade containers to fix $PYTHONPATH clashes in `fc_lane`, `inner_distance`, `tin`, `tin_merge`, and `rnaseq_multiqc`. (#176, @kelly-sovacool)
- Fix error that prevented existing output directories from being re-run. (#176, @kelly-sovacool)
- Fix error in `renee build` where `image_cache()` wasn't imported. (#178, @kelly-sovacool)

## RENEE 2.6.2

- Consolidate `build_cluster.json` into `cluster.json`. (#167, @kelly-sovacool)
- Remove unused miniconda container. (#168, @kelly-sovacool)
- Fix error in RSEQC rules. (#172, @kelly-sovacool)

## RENEE 2.6.1

- New contributing guide available on GitHub and the documentation website. (#159, @kelly-sovacool)
- New `renee debug` subcommand to determine the base directory for debugging purposes. (#159, @kelly-sovacool)
- Fix `renee cache` subcommand to correctly read the container images config file. (#163, @kelly-sovacool)

## RENEE 2.6.0

### New features

- Support hg38 release 45 on biowulf & FRCE. (#127, @kelly-sovacool)
- hg38 genome index files now include decoy & virus sequences. (#136, @kelly-sovacool)
  - Additionally, `--genome` is no longer required and is set to `hg38_36` by default.
- Set default shared singularity SIF directory for biowulf and frce. (#94, @kelly-sovacool)
- Add `renee gui` subcommand to launch the graphical user interface. (#94, @kelly-sovacool)
  - Previously, `renee_gui` (with an underscore) was a command in the `ccbrpipeliner` module.

### Bug fixes

- Ensure `renee build` creates necessary `config` directory during initialization. (#139, @kelly-sovacool)
- Run `rsem-generate-data-matrix` to create gene and isoform matrix files. (#149, @kelly-sovacool)
- Fix bug in the driver script that caused the snakemake module not to be loaded on biowulf in some cases. (#154, @kelly-sovacool)

### Documentation updates

- Minor documentation improvements. (#132, #135, #152, @kelly-sovacool)
- Add GUI instructions to the documentation website. (#38, @samarth8392)
- The docs website now has a dropdown menu to select which version to view. The latest release is shown by default. (#150, @kelly-sovacool)
- Show the name of the pipeline rather than the python script for CLI help messages. (#131, @kelly-sovacool)
- Added Expected output tab to the documentation website and updated FAQs (#156, @samarth8392)

## RENEE 2.5.13

- Backport all genome config files from v2.6.5. (#196, @kelly-sovacool)
  - Critical bug fix due to missing S3 bucket. (#191)
  - Rebuild hg19 & hg38 references from GDC. (#136)
  - Add marmoset genome. (#185)

## RENEE 2.5.12

- Minor documentation improvements. (#100, @kelly-sovacool)
- Fix RNA report bug, caused by hard-coding of PC1-3, when only PC1-2 were generated. (#104, @slsevilla)
- Allow printing the version or help message even if singularity is not in the path. (#110, @kelly-sovacool)
- Fix RSeQC environments:
  - Set RSeQC envmodule version to 4.0.0, which synchronizes it with the version in the docker container used by singularity. (#122, @kelly-sovacool)
  - Update docker with RSeQC's tools properly added to the path. (#123, @kelly-sovacool)

## RENEE 2.5.11

- Create a citation file to describe how to cite RENEE. (#86, @kelly-sovacool)
- Set HPC-specific fastq screen config and kraken DB paths for Biowulf and FRCE. (#78, @kelly-sovacool)
  - Previously, FRCE users were required to set `--shared-resources`,
    which were kept in a location on FRCE not under version control.
    This change brings the paths under version control so they're easier to recover if deleted.
- Fix permissions to allow read/write access to the scripts dir which caused rNA report to fail (#91, @slsevilla)
- Fix RSEM reference and rRNA interval list paths in FRCE-specific config files (#85, @kelly-sovacool & @slsevilla)
- Fix bug which caused incorrect genome annotation JSON files to be used (#87, @kelly-sovacool)
- Set default temporary directory depending on HPC platform. (#98, @kelly-sovacool)

## RENEE 2.5.10

- Fix a bug that caused slurm jobs to fail. (#74, @kopardev)

## RENEE 2.5.9

- Fix bugs that prevented single-end data from running through the pipeline. (#58, @kelly-sovacool)
- Increase wall time for kraken and bbmerge rules. (#68, @slsevilla)

## RENEE 2.5

- `SLURM_SUBMIT_HOST` adding to get hostname correctly on compute nodes.
- `config.json` is only created when runmode==init and is no longer recreated or overwritten when runmode==run or when resuming a previously unsuccessful run.
- prebuilt*list, a list of `<genome>*<gencode_annotation>` combos is auto-populated by glob-ing for relevant JSON files in the RENEEDIR/resources folder.

## RENEE 2.4

- "pipelinehome" added to `config.json` in output folder.
- `cluster.json` optimized.
- `"\.R1$", "\.R2$"` added to `workflow/scripts/pyparser.py`. This helps FQscreen2 output correctly collected in the `multiqc_matrix.tsv` which is required for rNA report HTML.

## RENEE 2.3

- `runner` orchestration script updated for:
  - `--wait` and `--create-nidap-folder` options added for _frce_. Also work on _biowulf_. These are required when running **RENEE** with NIDAP API call.
  - `--rerun-triggers mtime` set when _snakemake_ version is >= 7.8
- `spooker` updated to track user info on _frce_.
- _NIDAP_ folder related updates made to _Snakefile_. `rules/nidap.smk` added.
- "\_2" suffix added to "FQscreen2" files to distinguish them from "FQscreen" files. Now two separate fqscreen plots per sample are reported in the multiqc report.
- Custom Kraken2 database created and used. The "Standard" Kraken2 database was missing mouse genome.. hence it was added.

## RENEE v2.2

- `spooker` utility added to `onsuccess` and `onerror` blocks in `Snakefile`. Only works for _biowulf_.

## RENEE 2.1

- `spooker` utility added to track userdata on _biowulf_.
- CLI support for _frce_ implemented.
- resource jsons split into 2 folders _biowulf_ and _frce_ to store HPC-specific JSONs.
- resource bundles created on both, _biowulf_ and _frce_, for 4 **hg38** and 3 **mm10** genome+annotation combinations.

## RENEE 2.0

- new name **RENEE**
- `redirect` wrapper script added.
- MultiQC version changed from v1.9 to v1.12. `resources/multiqc_config.yaml` updated accordingly.
- updates to `project.json` and `tools.json` templates.
- updates to `builder`, `cacher` and `runner` workflow orchestration scripts.
- `resources/gff3togtf.py`, `resources/jobby` and `resources/run_jobby_on_snakemake_log` added.
- adding `jobby` related commands to `onsuccess` and `onerror` blocks in `Snakefile`.
- **fastQValidator**: `-minReadLen 2` added to command line.
- GTF now parsed at STAR command line. GTF-agnostic STAR index can be re-used saving significant disk space in the "resources" folder.
