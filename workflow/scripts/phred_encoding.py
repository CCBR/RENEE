#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import print_function, division
import sys
import gzip
from argparse import ArgumentParser

# Constants for Phred encoding detection
PHRED33_MIN_ASCII = 33
PHRED33_MAX_ASCII = 63
PHRED64_MIN_ASCII = 64
PHRED33_ENCODING = "33"
PHRED64_ENCODING = "64"
MAX_QUALITY_LINES_TO_CHECK = 10000
FASTQ_QUALITY_LINE_POSITION = 3


def usage(message="", exitcode=0):
    """Display help and usage information.

    Args:
        message: Optional error message to display
        exitcode: Exit code to use (0 for help, 1 for error)
    """
    print("Usage: python {} fastq_file".format(sys.argv[0]))
    if message:
        print(message)
    sys.exit(exitcode)


def reader(fname):
    """Return appropriate file handler for gzipped or uncompressed FastQ files.

    Args:
        fname: Path to FastQ file (.gz extension triggers gzip.open)

    Returns:
        File handler function (gzip.open or open)
    """
    return gzip.open if fname.endswith(".gz") else open


def detect_encoding_from_qscore(qscore):
    """Detect Phred encoding from a quality score string.

    Checks if quality score contains characters unique to Phred+33 (ASCII 33-63).

    Args:
        qscore: Quality score string from FastQ file

    Returns:
        str: "33" if Phred+33 characters found, None if ambiguous (all ASCII >= 64)
    """
    for char in qscore:
        ascii_val = ord(char)
        if ascii_val <= PHRED33_MAX_ASCII:
            # Found character unique to Phred+33
            return PHRED33_ENCODING

    # No unique Phred+33 characters found - ambiguous, needs more data
    return None


def get_min_ascii_in_string(text):
    """Get the minimum ASCII value in a string.

    Args:
        text: Input string

    Returns:
        int: Minimum ASCII value, or None if string is empty
    """
    if not text:
        return None
    return min(ord(char) for char in text)


def main(filename):
    """Determine the Phred encoding of a FastQ file.

    Samples up to MAX_QUALITY_LINES_TO_CHECK quality lines from the FastQ file
    to determine if it uses Phred+33 or Phred+64 encoding.

    Args:
        filename: Path to FastQ file (can be gzipped or uncompressed)

    Returns:
        str: "33" for Phred+33 encoding, "64" for Phred+64 encoding
    """
    handle = reader(filename)
    encoding = None
    min_ascii_seen = None
    quality_lines_checked = 0

    with handle(filename, "rt") as fastq:
        for line_num, line in enumerate(fastq):
            # Quality scores are at position 3 (0-indexed) in FastQ format
            if line_num % 4 == FASTQ_QUALITY_LINE_POSITION:
                line = line.strip()

                # Check for Phred+33 unique characters
                result = detect_encoding_from_qscore(line)
                if result == PHRED33_ENCODING:
                    # Found definitive Phred+33 character
                    return PHRED33_ENCODING

                # Track minimum ASCII value
                line_min_ascii = get_min_ascii_in_string(line)
                if line_min_ascii is not None:
                    if min_ascii_seen is None or line_min_ascii < min_ascii_seen:
                        min_ascii_seen = line_min_ascii

                quality_lines_checked += 1
                if quality_lines_checked >= MAX_QUALITY_LINES_TO_CHECK:
                    break

    # Determine encoding based on what we found
    if min_ascii_seen is not None and min_ascii_seen >= PHRED64_MIN_ASCII:
        # All quality scores were >= ASCII 64, likely Phred+64
        return PHRED64_ENCODING

    # Default to Phred+33 (modern standard) if uncertain
    return PHRED33_ENCODING


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Detect Phred encoding (33 or 64) of a FastQ file"
    )
    parser.add_argument("fastq_file", help="Path to FastQ file (can be gzipped)")

    args = parser.parse_args()
    encoding = main(args.fastq_file)
    print(encoding)
