# Version Notes

## v2.5

- `SLURM_SUBMIT_HOST` adding to get hostname correctly on compute nodes.

## v2.4

 - "pipelinehome" added to `config.json` in output folder.
 - `cluster.json` optimized.
 - `"\.R1$", "\.R2$"` added to `workflow/scripts/pyparser.py`. This helps FQscreen2 output correctly collected in the `multiqc_matrix.tsv` which is required for rNA report HTML.

## v2.3

 - `runner` orchestration script updated for:
   - `--wait` and `--create-nidap-folder` options added for _frce_. Also work on _biowulf_. These are required when running **RENEE** with NIDAP API call.
   - `--rerun-triggers mtime` set when _snakemake_ version is >= 7.8
 - `spooker` updated to track user info on _frce_.
 - _NIDAP_ folder related updates made to _Snakefile_. `rules/nidap.smk` added.
 - "_2" suffix added to "FQscreen2" files to distinguish them from "FQscreen" files. Now two separate fqscreen plots per sample are reported in the multiqc report.
 - Custom Kraken2 database created and used. The "Standard" Kraken2 database was missing mouse genome.. hence it was added.

## v2.2

 - `spooker` utility added to `onsuccess` and `onerror` blocks in `Snakefile`. Only works for _biowulf_.

## v2.1

 - `spooker` utility added to track userdata on _biowulf_.
 - CLI support for _frce_ implemented.
 - resource jsons split into 2 folders _biowulf_ and _frce_ to store HPC-specific JSONs.
 - resource bundles created on both, _biowulf_ and _frce_, for 4 **hg38** and 3 **mm10** genome+annotation combinations.

## v2.0

 - new name **RENEE**
 - `redirect` wrapper script added.
 - MultiQC version changed from v1.9 to v1.12. `resources/multiqc_config.yaml` updated accordingly.
 - updates to `project.json` and `tools.json` templates.
 - updates to `builder`, `cacher` and `runner` workflow orchestration scripts.
 - `resources/gff3togtf.py`, `resources/jobby` and `resources/run_jobby_on_snakemake_log` added.
 - adding `jobby` related commands to `onsuccess` and `onerror` blocks in `Snakefile`.
 - **fastQValidator**: `-minReadLen 2` added to command line.
 - GTF now parsed at STAR command line. GTF-agnostic STAR index can be re-used saving significant disk space in the "resources" folder.
