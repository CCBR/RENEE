#!/usr/bin/env Rscript

# USAGE: Rscript rNA.R -m src/rNA.Rmd -r data/TCGA-GBM_Raw_RSEM_Genes.txt -t data/TCGA-GBM_TINs.txt -q data/multiqc_matrix.txt -o "$PWD"

library(argparse)

# Parse Args
parser <- ArgumentParser()

# rNA Rmarkdown file
parser$add_argument("-m", "--rmarkdown", type="character", required=TRUE,
                    help="Required Input File: rNA Rmarkdown file")

# Raw Counts Matrix
parser$add_argument("-r", "--raw_counts", type="character", required=TRUE,
                    help="Required Input File: Raw counts matrix")

# TIN Counts Matrix
parser$add_argument("-t", "--tin_counts", type="character", required=TRUE,
                    help="Required Input File: TIN counts matrix")

# QC Metadata Table
parser$add_argument("-q", "--qc_table", type="character", required=TRUE,
                    help="Required Input File: QC Metadata Table")

# Output HTML Filename
parser$add_argument("-f", "--output_filename", type="character", required=FALSE, default = 'rNA.html',
                    help="Optional Output HTML Filename: Defaults to 'rNA.html'")

# Display sample names
parser$add_argument("-a", "--annotate", action="store_true", default=FALSE,
    help="Display sample names in complex heatmap: Defaults to FALSE")

args <- parser$parse_args()

# Generate HTML output
rmarkdown::render(args$rmarkdown, output_file=args$output_filename, params = list(
  raw = args$raw_counts,
  tin = args$tin_counts,
  qc = args$qc_table,
  annot = args$annotate
 )
)