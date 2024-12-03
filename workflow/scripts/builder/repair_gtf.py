#!/usr/bin/env python
import sys
import collections
import gzip
import HTSeq
import functools
import sys


def get_open_func(filename):
    return functools.partial(gzip.open, mode="rt") if filename.endswith(".gz") else open


def retrieve_header(in_filename):
    open_func = get_open_func(in_filename)
    with open_func(in_filename) as file_handle:
        header = list()
        for line in file_handle:
            if line.startswith("#"):
                header.append(line)
            else:
                break
    return header


def build_genes_dict(in_filename):
    """
    Create a dictionary mapping gene IDs to feature objects from HTSeq.GFF_Reader
    """
    open_func = get_open_func(in_filename)
    with open_func(in_filename) as gtf_file:
        gtf_file = HTSeq.GFF_Reader(gtf_file)
        genes_dict = {}
        for feature in gtf_file:
            if feature.type == "gene":
                gene_id = feature.attr["gene_id"]
                if gene_id in genes_dict:
                    raise KeyError(f"Duplicate gene ID found: {gene_id}")
                genes_dict[gene_id] = feature
    return genes_dict


def fix_exon_attrs(exon_feature, genes_dict, debug=True):
    """
    If exon_feature does not have 'gene_type' or 'gene_biotype', retrieve them from the gene feature
    """
    biotypes = ["gene_type", "gene_biotype"]
    if not any(key in exon_feature.attr for key in biotypes):
        debug_msg = f"Exon {exon_feature.attr['gene_id']} missing 'gene_type' or 'gene_biotype'. Adding "
        gene = genes_dict[exon_feature.attr["gene_id"]]
        if "gene_type" in gene.attr:
            exon_feature.attr["gene_type"] = gene.attr["gene_type"]
            debug_msg += f"'gene_type'={gene.attr['gene_type']} "
        if "gene_biotype" in gene.attr:
            exon_feature.attr["gene_biotype"] = gene.attr["gene_biotype"]
            debug_msg += f"'gene_biotype'={gene.attr['gene_biotype']} "
        if not any(key in gene.attr for key in biotypes):
            raise KeyError(
                f"Gene {exon_feature.attr['gene_id']} does not have 'gene_type' or 'gene_biotype'"
            )
        if debug:
            print(debug_msg)
    return exon_feature


def repair_gtf(in_filename, out_filename, debug=False):
    # build a dictionary of gene features
    genes_dict = build_genes_dict(in_filename)

    # iterate over features and add gene_type/biotype if needed
    new_gtf_lines = retrieve_header(in_filename)
    open_func = get_open_func(in_filename)
    with open_func(in_filename) as gtf_file:
        gtf_file = HTSeq.GFF_Reader(gtf_file)
        for feature in gtf_file:
            if feature.type == "exon":
                feature = fix_exon_attrs(feature, genes_dict, debug=debug)
            new_gtf_lines.append(feature.get_gff_line())

    # write the new GTF file
    with open(out_filename, "w") as out_file:
        out_file.writelines(new_gtf_lines)


if __name__ == "__main__":
    if "snakemake" in locals() or "snakemake" in globals():
        in_filename = snakemake.input.gtf
        out_filename = snakemake.output.gtf
    else:
        in_filename = sys.argv[1]
        out_filename = sys.argv[2]
    repair_gtf(in_filename, out_filename)

test_cmd = """
/data/CCBR_Pipeliner/Pipelines/RENEE/renee-dev-sovacool/bin/renee build \
    --sif-cache /data/CCBR_Pipeliner/SIFs \
    --ref-fa /data/CCBR_Pipeliner/db/PipeDB/GDC_refs/downloads/GRCh38.d1.vd1.fa \
    --ref-name hg38 \
    --ref-gtf /data/CCBR_Pipeliner/db/PipeDB/Indices/GTFs/hg38/gencode.v45.primary_assembly.annotation.gtf \
    --gtf-ver v45-test \
    --output /data/CCBR_Pipeliner/db/PipeDB/Indices/test
"""
