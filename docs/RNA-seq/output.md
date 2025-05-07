After a successful `renee` run execution for multisample paired-end data, the following files and folders are created in the output folder.

```bash
renee_output/
├── bams
├── config 
├── config.json # Contains the configuration and parameters used for this specific RENEE run
├── DEG_ALL
├── dryrun.{datetime}.log # Output from the dry-run of the pipeline
├── FQscreen
├── FQscreen2
├── fusions
├── kraken
├── logfiles 
├── nciccbr 
├── preseq 
├── QC
├── QualiMap
├── rawQC
├── Reports
├── resources
├── RSeQC
├── sample1.R1.fastq.gz -> /path/to/input/fastq/files/sample1.R1.fastq.gz
├── sample1.R2.fastq.gz -> /path/to/input/fastq/files/sample1.R2.fastq.gz
...
..
.
├── sampleN.R1.fastq.gz -> /path/to/input/fastq/files/sampleN.R1.fastq.gz
├── sampleN.R2.fastq.gz -> /path/to/input/fastq/files/sampleN.R2.fastq.gz
├── STAR_files
├── trim
└── workflow
```

## Folder details and file descriptions

### 1. `bams`

Contains the STAR aligned reads for each sample analyzed in the run.

```bash
/bams/
├── sample1.fwd.bw # forward strand bigwig files suitable for a genomic track viewer like IGV
├── sample1.rev.bw # reverse strand bigwig files 
├── sample1.p2.Aligned.toTranscriptome.out.bam # BAM alignments to transcriptome using STAR in two-pass mode
├── sample1.star_rg_added.sorted.dmark.bam # Read groups added and duplicates marked genomic BAM file (using STAR in two-pass mode)
├── sample1.star_rg_added.sorted.dmark.bam.bai
...
..
.
```

### 2. `config`

Contains config files for the pipeline.


### 3. `DEG_ALL`

Contains the output from RSEM estimating gene and isoform expression levels for each sample and also combined data matrix with all samples.

```bash
/DEG_ALL/
├── combined_TIN.tsv # RSeQC logfiles containing transcript integrity number information for all samples
├── RSEM.genes.expected_count.all_samples.txt # Expected gene counts matrix for all samples (useful for downstream differential expression analysis)
├── RSEM.genes.expected_counts.all_samples.reformatted.tsv # Expected gene counts matrix for all samples with reformatted gene symbols (format: ENSEMBLID | GeneName)
├── RSEM.genes.FPKM.all_samples.txt # FPKM Normalized expected gene counts matrix for all samples 
├── RSEM.genes.TPM.all_samples.txt # TPM Normalized expected gene counts matrix for all samples
├── RSEM.isoforms.expected_count.all_samples.txt # File containing isoform level expression estimates for all samples.
├── RSEM.isoforms.FPKM.all_samples.txt # FPKM Normalized expected isoform counts matrix for all samples 
├── RSEM.isoforms.TPM.all_samples.txt # TPM Normalized expected isoform counts matrix for all samples
├── sample1.RSEM.genes.results # Expected gene counts for sample 1
├── sample1.RSEM.isoforms.results # Expected isoform counts for sample 1
├── sample1.RSEM.stat # RSEM stats for sample 1
│   ├── sample1.RSEM.cnt 
│   ├── sample1.RSEM.model
│   └── sample1.RSEM.theta
├── sample1.RSEM.time # Run time log for sample 1
...
..
.
├── sampleN.RSEM.genes.results
├── sampleN.RSEM.isoforms.results
├── sampleN.RSEM.stat
│   ├── sampleN.RSEM.cnt
│   ├── sampleN.RSEM.model
│   └── sampleN.RSEM.theta
└── sampleN.RSEM.time

```

### 4. `FQScreen` and `FQScreen2`

These folders contain results from quality-control step to screen for different sources of contamination. FastQ Screen compares your sequencing data to a set of different reference genomes to determine if there is contamination. It allows a user to see if the composition of your library matches what you expect. These results are plotted in the multiQC report.

### 5. `fusions`

Contains gene fusions output for each sample.

```bash
fusions/
├── sample1_fusions.arriba.pdf
├── sample1_fusions.discarded.tsv # Contains all events that Arriba classified as an artifact or that are also observed in healthy tissue. 
├── sample1_fusions.tsv # Contains fusions for sample 1 which pass all of Arriba's filters. The predictions are listed from highest to lowest confidence. 
├── sample1.p2.arriba.Aligned.sortedByCoord.out.bam # Sorted BAM file for Arriba's Visualization
├── sample1.p2.arriba.Aligned.sortedByCoord.out.bam.bai
├── sample1.p2.Log.final.out # STAR final log file
├── sample1.p2.Log.out # STAR runtime log file
├── sample1.p2.Log.progress.out # log files
├── sample1.p2.Log.std.out # STAR runtime output log
├── sample1.p2.SJ.out.tab #  Summarizes the high confidence splice junctions for sample 1
├── sample1.p2._STARgenome # Extra files generated during STAR aligner 
│   ├── exonGeTrInfo.tab
│   ├── .
│   ├── .
│   └── transcriptInfo.tab 
├── sample1.p2._STARpass1 # Extra files generated during STAR first pass 
│   ├── .
│   └── .
...
..
.

```

### 6. `kraken`

Contains per sample kraken output files which is a Quality-control step to assess for potential sources of microbial contamination. Kraken is used in conjunction with Krona to produce an interactive reports stored in `.krona.html` files. These results are present in the multiQC report.

### 7. `logfiles`

Contains logfiles for the entire RENEE run, job error/output files for each individual job that was submitted to SLURM, and some other stats generated by different software. Important to diagnose errors if the pipeline fails. The per sample stats information is present in the mulitQC report. 

```bash
/logfiles/
├── master.log # Logfile for the main (master) RENEE job
├── mjobid.log # SLURM JOBID for the master RENEE job
├── runtime_statistics.json # Runtime statistics for each rule in the RENEE run
├── sample1.flagstat.concord.txt # sample mapping stats
├── sample1.p2.Log.final.out # sample STAR alignment stats
├── sample1.RnaSeqMetrics.txt # sample stats collected by Picard CollectRnaSeqMetrics
├── sample1.star.duplic # Mark duplicate metrics
...
..
.
├── slurmfiles
│   ├── {MASTER_JOBID}.{JOBID}.{rule}.{wildcards}.out
│   ├── {MASTER_JOBID}.{JOBID}.{rule}.{wildcards}.err
│   ...
│   ..
│   .
├── snakemake.log # The snakemake log file which documents the entire pipeline log
├── snakemake.log.jobby # Detailed summary report for each individual job. 
└── snakemake.log.jobby.short # Short summary report for each individual job. 
```

### 8. `nciccbr`

Contain Arriba resources for gene fusion estimation. Manually curated and only exist for a few reference genomes (mm10, hg38, hg19).

### 9. `preseq`

Contains library complexity curves for each sample. These results are part of the multiQC report.

### 10. `QC` and `rawQC`

Contains per sample output from FastQC for raw and adapter trimmed fastq files with insert size estimates. These results are part of the multiQC report.

### 11. `QualiMap`

Contains per sample output for Quality-control step to assess various post-alignment metrics and a secondary method to calculate insert size. These results are part of the multiQC report.

### 12. `Reports`

Contains the multiQC report which visually summarizes the quality control metrics and other statistics for each sample (`multiqc_report.html`). All the data tables used to generate the multiQC report is available in the `multiqc_data` folder.  The `RNA_report.html` file is an interactive report the aggregates sample quality-control metrics across all samples. This interactive report to allow users to identify problematic samples prior to downstream analysis. It uses flowcell and lane information from the FastQ file.

### 13. `resources`

Contains resources necessary to run the RENEE pipeline.

### 14. `RSeQC`

Contains various QC metrics for each sample collected by RSeQC. These results are part of the multiQC report.

### 15. `STAR_files`

Contains log files, splice junction tab file (`SJ.out.tab`), and `ReadsPerGene.out.tab` file, and other various output files for each sample generated by STAR aligner.

### 16. `trim`

Contains adapter trimmed FASTQ files for each sample used for all the downstream analysis.

```bash
trim
├── sample1.R1.trim.fastq.gz
├── sample1.R2.trim.fastq.gz
...
..
.
├── sampleN.R1.trim.fastq.gz
└── sampleN.R2.trim.fastq.gz

```

### 17. `workflow`

Contains the RENEE pipeline workflow.