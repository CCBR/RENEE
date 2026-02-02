#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Unit tests for phred_encoding.py script.

Tests ensure correct detection of Phred+33 and Phred+64 quality score encodings
in FastQ files.
"""

import pytest
import sys
import os
import gzip
import tempfile
from pathlib import Path

# Add the workflow/scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "workflow" / "scripts"))

from phred_encoding import detect_encoding_from_qscore, reader, main


class TestDetectEncodingFromQScore:
    """Test the detect_encoding_from_qscore() function with various quality score strings."""

    def test_phred33_with_unique_chars_low_quality(self):
        """Test Phred+33 quality scores with unique low-quality characters."""
        # Characters like !, ", #, $, etc. (ASCII 33-39) only exist in Phred+33
        qscore = "!!###$$$%%%"
        assert detect_encoding_from_qscore(qscore) == "33"

    def test_phred33_with_unique_chars_mid_quality(self):
        """Test Phred+33 quality scores with unique mid-quality characters."""
        # Characters like +, -, ., / (ASCII 43-47) only exist in Phred+33
        qscore = "+++---...///"
        assert detect_encoding_from_qscore(qscore) == "33"

    def test_phred33_with_unique_chars_numbers(self):
        """Test Phred+33 quality scores with digit characters."""
        # Digits 0-9 and : ; < = > ? (ASCII 48-63) only exist in Phred+33
        qscore = "0123456789:;<=>?"
        assert detect_encoding_from_qscore(qscore) == "33"

    def test_phred33_modern_illumina(self):
        """Test modern Illumina Phred+33 quality scores."""
        # Modern Illumina with some low-quality characters
        qscore = "AAAFFJJFJJJJJJFJJJJJJJJJJFJAJJJJJFJJJJJFFJJAJJJJ7JJ"
        assert detect_encoding_from_qscore(qscore) == "33"

    def test_phred33_with_comma(self):
        """Test Phred+33 with comma character (common in lower quality reads)."""
        # Comma (ASCII 44) is unique to Phred+33
        qscore = ",AFFFFKKKKFKKKKKKKKKKK"
        assert detect_encoding_from_qscore(qscore) == "33"

    def test_phred33_mixed_quality(self):
        """Test Phred+33 with mixed quality characters."""
        qscore = "IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII9IG9ICIIIIIIIIIIIIIIIIIIII"
        assert detect_encoding_from_qscore(qscore) == "33"

    def test_ambiguous_high_quality_returns_none(self):
        """Test that high-quality scores only (ASCII 64+) return None (ambiguous)."""
        # Only characters that could be in both encodings
        qscore = "@@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghi"
        assert detect_encoding_from_qscore(qscore) is None

    def test_all_high_quality_K(self):
        """Test quality string with only K characters (ambiguous, returns None)."""
        qscore = "KKKKKKKKKKKKKKKKKKKK"
        assert detect_encoding_from_qscore(qscore) is None

    def test_empty_string(self):
        """Test empty quality score string returns None."""
        qscore = ""
        assert detect_encoding_from_qscore(qscore) is None

    def test_single_unique_phred33_char(self):
        """Test that even a single unique Phred+33 character is detected."""
        # One unique Phred+33 character (!) among ambiguous characters
        qscore = "KKKKKKKKK!KKKKKKKK"
        assert detect_encoding_from_qscore(qscore) == "33"


class TestReaderFunction:
    """Test the reader() function for file handling."""

    def test_reader_gzipped_file(self):
        """Test that reader returns gzip.open for .gz files."""
        fname = "test.fastq.gz"
        assert reader(fname) == gzip.open

    def test_reader_uncompressed_file(self):
        """Test that reader returns open for non-.gz files."""
        fname = "test.fastq"
        assert reader(fname) == open


class TestFullWorkflow:
    """Test the full workflow with actual temporary FastQ files."""

    def test_phred33_fastq_uncompressed(self):
        """Test detection with uncompressed Phred+33 FastQ file."""
        # Create a temporary uncompressed FastQ file with Phred+33 encoding
        content = """@SEQ_ID_1
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
!''*((((***+))%%%++)(%%%%).1***-+*''))**55CCF>>>>>>CCCCCCC65
@SEQ_ID_2
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII9IG9ICIIIIIIIIIIIIIIIIIIII
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fastq", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            assert encoding == "33"
        finally:
            os.unlink(temp_file)

    def test_phred33_fastq_compressed(self):
        """Test detection with gzipped Phred+33 FastQ file."""
        # Create a temporary gzipped FastQ file with Phred+33 encoding
        content = b"""@SEQ_ID_1
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
!''*((((***+))%%%++)(%%%%).1***-+*''))**55CCF>>>>>>CCCCCCC65
@SEQ_ID_2
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
AAAFFJJFJJJJJJFJJJJJJJJJJFJAJJJJJFJJJJJFFJJAJJJJ7JJJJJJJJJJ
"""
        with tempfile.NamedTemporaryFile(suffix=".fastq.gz", delete=False) as f:
            with gzip.open(f.name, "wb") as gz:
                gz.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            assert encoding == "33"
        finally:
            os.unlink(temp_file)

    def test_phred64_like_fastq(self):
        """Test detection with FastQ file using only Phred+64 characters."""
        # Only use characters ASCII 64+ (Phred+64 encoded)
        # Should be detected as Phred+64
        content = """@SEQ_ID_1
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
@@BCDEFGHIJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ
@SEQ_ID_2
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
@SEQ_ID_3
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
@@@@BBBBCCCCDDDDEEEEFFFFGGGGHHHHIIIIJJJJKKKKLLLLMMMMNNNNOOO
@SEQ_ID_4
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fastq", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            assert encoding == "64"
        finally:
            os.unlink(temp_file)

    def test_modern_illumina_real_world(self):
        """Test with real-world modern Illumina quality scores."""
        # Based on actual Illumina HiSeq/NovaSeq data
        content = b"""@K00193:38:H3MYFBBXX:4:1101:10003:44458/1
TTCCTTATGAAACAGGAAGAGTCCCTGGGCCCAGGCCTGGCCCACGGTTGT
+
AAFFFKKKKKKKKKKKKKKKKKKKKKKKKFKKFKKKKF<AAKKKKKKKKKKK
@K00193:38:H3MYFBBXX:4:1101:10003:46427/1
CGCCTGGCGACCTTGGTGTCCGCGATGTGGATCATGTCCTTATCAATGTAG
+
,AFFFFKKKKFKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK
"""
        with tempfile.NamedTemporaryFile(suffix=".fastq.gz", delete=False) as f:
            with gzip.open(f.name, "wb") as gz:
                gz.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            # Should detect Phred+33 due to '<' and ',' characters
            assert encoding == "33"
        finally:
            os.unlink(temp_file)


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_low_quality_phred33(self):
        """Test very low quality Phred+33 scores (ASCII 33-40)."""
        qscore = "!\"#$%&'()"
        assert detect_encoding_from_qscore(qscore) == "33"

    def test_boundary_character_question_mark(self):
        """Test '?' character (ASCII 63, last unique Phred+33 character)."""
        qscore = "???????????"
        assert detect_encoding_from_qscore(qscore) == "33"

    def test_boundary_character_at_sign(self):
        """Test '@' character (ASCII 64, first ambiguous character)."""
        qscore = "@@@@@@@@@@@"
        assert detect_encoding_from_qscore(qscore) is None  # Ambiguous, returns None

    def test_mixed_unique_and_ambiguous(self):
        """Test mix of unique Phred+33 and ambiguous characters."""
        qscore = "AAAFFF###JJJJJJ"
        assert detect_encoding_from_qscore(qscore) == "33"

    def test_single_character_unique(self):
        """Test single unique Phred+33 character."""
        qscore = "!"
        assert detect_encoding_from_qscore(qscore) == "33"

    def test_single_character_ambiguous(self):
        """Test single ambiguous character returns None."""
        qscore = "K"
        assert detect_encoding_from_qscore(qscore) is None


class TestPhred64Detection:
    """Test cases specifically for Phred+64 detection."""

    def test_phred64_fastq_compressed(self):
        """Test detection of true Phred+64 encoded gzipped FastQ."""
        # Phred+64 file - only ASCII 64+ characters
        content = b"""@SEQ_ID_1
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
@@BCDEFGHIJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ
@SEQ_ID_2
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
@SEQ_ID_3
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
@@@BBBCCCDDDEEEFFFGGGHHHIIIJJJKKKLLLMMMNNNOOOPPPQQQRRRSSSTTT
"""
        with tempfile.NamedTemporaryFile(suffix=".fastq.gz", delete=False) as f:
            with gzip.open(f.name, "wb") as gz:
                gz.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            assert encoding == "64"
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
