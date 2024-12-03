## tiny test genome

https://raw.githubusercontent.com/nf-core/test-datasets/atacseq/reference/genome.fa

https://raw.githubusercontent.com/nf-core/test-datasets/atacseq/reference/genes.gtf

```sh
workflow/scripts/builder/generate_qualimap_ref.py -g tests/data/genomes/tiny/genes.gtf.gz -f tests/data/genomes/tiny/genome.fa.gz -o tests/dat
a/genomes/tiny/qualimap_info.txt --ignore-strange-chrom
```
