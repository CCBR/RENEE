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

    # parse GTF file
    open_func = get_open(gtfFileName)
    with open_func(gtfFileName) as gtf_file:
        gtf_file = HTSeq.GFF_Reader(gtf_file)
        features = {}
        for feature in gtf_file:
            if feature.type == "exon":
                geneName = feature.attr["gene_id"]
                if geneName in features:
                    features[geneName].append(feature)
                else:
                    features[geneName] = [feature]

    # load & save sequences
    open_func = get_open(fastaFileName)
    with open_func(fastaFileName) as fasta_file:
        seqData = SeqIO.to_dict(SeqIO.parse(fasta_file, "fasta"))

    outFile = open(outFileName, "w")
    header = '"%s"\t"%s"\t"%s"\n' % ("biotypes", "length", "gc")
    outFile.write(header)

    for geneId in features:
        exons = features[geneId]
        print("Processing %s" % geneId)

        if len(exons) == 0:
            continue
        try:
            biotype = exons[0].attr["gene_type"]
        except KeyError:
            biotype = exons[0].attr["gene_biotype"]
        length = 0
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

        gc_array = []
        lengths = []

        for tSeq in transcripts.values():
            lengths.append(len(tSeq))
            gc_array.append(GC(tSeq))

        gene_length = np.mean(lengths)
        gene_gc = np.mean(gc_array)

        line = '"%s"\t"%s"\t%d\t%.2f\n' % (geneId, biotype, gene_length, gene_gc)
        outFile.write(line)

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
