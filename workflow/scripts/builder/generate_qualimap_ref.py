#!/usr/bin/env python
from __future__ import print_function
from Bio import SeqIO
from Bio.Seq import Seq
import sys
import argparse
import collections
import gzip
import HTSeq
import functools
import numpy as np

# GC was deprecated in favor of gc_fraction from Biopython 1.82
# https://github.com/nextgenusfs/funannotate/issues/1000
try:
    from Bio.SeqUtils import gc_fraction

    def GC(sequence):
        return 100 * gc_fraction(sequence, ambiguous="ignore")

except ImportError:
    from Bio.SeqUtils import GC


def get_open(filename):
    return functools.partial(gzip.open, mode="rt") if filename.endswith(".gz") else open


def idsContainGiven(givenId, transcriptIds):
    for tId in transcriptIds:
        if givenId.find(tId) != -1:
            return True

    return False


def write_qualimap_info(args):
    gtfFileName = args.gtfFile
    fastaFileName = args.fastaFile
    outFileName = args.outFile

    if args.filterStr:
        filtered_transcripts = args.filterStr.split(",")
        if filtered_transcripts:
            print("Filtering for: ", filtered_transcripts)

    # load fasta sequences
    open_func = get_open(fastaFileName)
    with open_func(fastaFileName) as fasta_file:
        seqData = SeqIO.to_dict(SeqIO.parse(fasta_file, "fasta"))

    # parse GTF file
    open_func = get_open(gtfFileName)
    with open_func(gtfFileName) as gtf_file:
        gtf_file = HTSeq.GFF_Reader(gtf_file)
        exons_dict = collections.defaultdict(list)
        other_features = []
        for feature in gtf_file:
            if feature.type == "exon":
                geneName = feature.attr["gene_id"]
                exons_dict[geneName].append(feature)
    outFile = open(outFileName, "w")
    outFile.write(f'"biotypes"\t"length"\t"gc"\n')

    for geneId, exons in exons_dict.items():
        print("Processing %s" % geneId)

        if len(exons) == 0:
            continue

        biotypes = ["gene_type", "gene_biotype"]
        biotype = None
        for biotype_str in biotypes:
            if biotype_str in exons[0].attr:
                biotype = exons[0].attr[biotype_str]
                break
        if not biotype:
            raise ValueError(
                f"No biotype found for exon {exons[0].attr['transcript_id']}. Exons must have at least one of these attributes: {', '.join(biotypes)}"
            )

        # build transcripts dictionary
        transcripts = {}
        for exon in exons:
            transcriptId = exon.attr["transcript_id"]
            tSeq = transcripts.get(transcriptId, Seq(""))

            iv = exon.iv
            seqName = iv.chrom
            if seqName in seqData:
                buf = seqData[iv.chrom].seq[iv.start : iv.end]
                if iv.strand == "-":
                    buf = buf.reverse_complement()
                tSeq += buf
            else:
                print(
                    "Can not locate sequence {} in {}, skipping region...".format(
                        seqName, fastaFileName
                    )
                )
            transcripts[transcriptId] = tSeq

        gc_array = [GC(tSeq) for tSeq in transcripts.values()]
        lengths = [len(tSeq) for tSeq in transcripts.values()]

        gene_length_mean = int(np.mean(lengths))
        gene_gc_mean = "{:.2f}".format(round(np.mean(gc_array), 2))

        outFile.write(f'"{geneId}"\t"{biotype}"\t{gene_length_mean}\t{gene_gc_mean}\n')

    outFile.close()


if __name__ == "__main__":
    descriptionText = "The script extracts features from a GTF file and a FASTA file into Qualimap annotation format. Note: exons have to be sorted according to exon number! This important for correct reverse transcribed cDNA sequences extraction."
    parser = argparse.ArgumentParser(
        description=descriptionText,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-g",
        action="store",
        required="true",
        dest="gtfFile",
        help="Input file with list of genes in GTF format",
    )
    parser.add_argument(
        "-f",
        action="store",
        required="true",
        dest="fastaFile",
        help="Input genome sequence. ",
    )
    parser.add_argument(
        "-o",
        action="store",
        dest="outFile",
        default="annotations.txt",
        help="Output file. Default is annotations.txt",
    )
    parser.add_argument(
        "--filter",
        action="store",
        dest="filterStr",
        default="",
        help="Comma-separted list of entries to filter from GTF file based on given attribute id",
    )
    parser.add_argument(
        "--ignore-strange-chrom",
        action="store_true",
        default=False,
        dest="ignoreStrangeChromosomes",
        help="All chromosomes except numbered and X,Y,MT are ignored ",
    )
    args = parser.parse_args()
    print(args)
    write_qualimap_info(args)
