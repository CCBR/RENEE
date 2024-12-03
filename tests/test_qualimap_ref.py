import argparse
import filecmp
import hashlib
import HTSeq
import tempfile
import time

from ccbr_tools.pipeline.util import get_hpcname
from ccbr_tools.shell import shell_run
from renee.workflow.scripts.builder.generate_qualimap_ref import write_qualimap_info


qualimap_cmd = """workflow/scripts/builder/generate_qualimap_ref.py \
-g {gtf} \
-f {fasta} \
-o {outfile} \
--ignore-strange-chrom
"""


def filter_by_qualimap(gtf_filename, qualimap_filename, out_filename=""):
    """
    Filter a GTF file based on entries in a qualimap file.
    """
    with open(qualimap_filename) as infile:
        next(infile)
        gene_entries = [line.split("\t")[0].strip('"') for line in infile]
    gtf_file = HTSeq.GFF_Reader(gtf_filename)

    if not out_filename:
        out_filename = gtf_filename.replace(".gtf", ".filtered.gtf")
        assert out_filename != gtf_filename

    with open(out_filename, "w") as out_file:
        for feature in gtf_file:
            if feature.type == "exon":
                gene_name = feature.attr["gene_id"]
                if gene_name in gene_entries:
                    out_file.write(feature.get_gff_line())


def create_mouse_subset():
    mouse_gtf = (
        "/data/CCBR_Pipeliner/db/PipeDB/Indices/GTFs/mm10/gencode.vM21.annotation.gtf"
    )

    mouse_fa = "/data/CCBR_Pipeliner/db/PipeDB/Indices/mm10_basic/indexes/mm10.fa"
    shell_run(
        qualimap_cmd.format(gtf=mouse_gtf, fasta=mouse_fa, outfile="qualimap_info.txt")
    )
    filter_by_qualimap(
        gtf_filename=mouse_gtf,
        qualimap_filename="tests/data/genomes/mm10_M21.subset.qualimap_info.txt",
        out_filename="tests/data/genomes/M21.subset.gtf",
    )
    shell_run(
        qualimap_cmd.format(
            gtf="tests/data/genomes/M21.subset.gtf",
            fasta=mouse_fa,
            outfile="tests/data/genomes/qualimap_info.subset.txt",
        )
    )
    assert filecmp.cmp(
        "tests/data/genomes/qualimap_info.subset.txt",
        "tests/data/genomes/mm10_M21.subset.qualimap_info.txt",
        shallow=False,
    )


def run_qualimap_comp(fasta, gtf, oracle):
    with tempfile.TemporaryDirectory() as tmp_dir:
        outfile = f"{tmp_dir}/qualimap_info.txt"
        args = argparse.Namespace(
            gtfFile=gtf,
            fastaFile=fasta,
            outFile=outfile,
            filterStr="",
            ignoreStrangeChromosomes=True,
        )
        write_qualimap_info(args)
        result = filecmp.cmp(outfile, oracle, shallow=False)
    return result


def test_qualimap_ref_tiny():
    assert run_qualimap_comp(
        "tests/data/genomes/tiny/genome.fa.gz",
        "tests/data/genomes/tiny/genes.gtf.gz",
        "tests/data/genomes/tiny/qualimap_info.txt",
    )


if get_hpcname() == "biowulf":

    def test_qualimap_ref_mouse():
        assert run_qualimap_comp(
            "/data/CCBR_Pipeliner/db/PipeDB/Indices/mm10_basic/indexes/mm10.fa",
            "tests/data/genomes/M21.subset.gtf.gz",
            "tests/data/genomes/mm10_M21.subset.qualimap_info.txt",
        )


if __name__ == "__main__":
    # generate test snapshots
    start = time.perf_counter()
    shell_run(
        qualimap_cmd.format(
            gtf="tests/data/genomes/tiny/genes.gtf.gz",
            fasta="tests/data/genomes/tiny/genome.fa.gz",
            outfile="tests/data/genomes/tiny/qualimap_info.txt",
        )
    )
    shell_run(
        qualimap_cmd.format(
            gtf="tests/data/genomes/M21.subset.gtf.gz",
            fasta="/data/CCBR_Pipeliner/db/PipeDB/Indices/mm10_basic/indexes/mm10.fa",
            outfile="tests/data/genomes/mm10_M21.subset.qualimap_info.txt",
        )
    )
    end = time.perf_counter()
    print("elapsed", end - start)
