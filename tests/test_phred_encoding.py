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
from unittest.mock import patch

# Add the workflow/scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "workflow" / "scripts"))

from phred_encoding import (
    detect_encoding_from_qscore,
    reader,
    main,
    get_min_ascii_in_string,
    usage,
)


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


class TestGetMinAsciiInString:
    """Test the get_min_ascii_in_string() helper function."""

    def test_get_min_ascii_basic(self):
        """Test minimum ASCII value in a string."""
        text = "JJJJJJJ"
        result = get_min_ascii_in_string(text)
        assert result == ord("J")

    def test_get_min_ascii_with_low_chars(self):
        """Test with characters including Phred+33 unique chars."""
        text = "JJJ!JJJJ"
        result = get_min_ascii_in_string(text)
        assert result == ord("!")

    def test_get_min_ascii_single_char(self):
        """Test with single character string."""
        text = "K"
        result = get_min_ascii_in_string(text)
        assert result == ord("K")

    def test_get_min_ascii_empty_string(self):
        """Test with empty string returns None."""
        text = ""
        result = get_min_ascii_in_string(text)
        assert result is None

    def test_get_min_ascii_all_same_chars(self):
        """Test with all identical characters."""
        text = "AAAAAAA"
        result = get_min_ascii_in_string(text)
        assert result == ord("A")


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

    def test_reader_various_extensions(self):
        """Test reader with various file extensions."""
        # Should return open for non-.gz files
        assert reader("file.fq") == open
        assert reader("file.txt") == open
        assert reader("file.fastq.bak") == open
        # Should return gzip.open for .gz files
        assert reader("file.gz") == gzip.open
        assert reader("archive.tar.gz") == gzip.open


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


class TestUsageFunction:
    """Test the usage() help function."""

    def test_usage_help_message(self):
        """Test usage function with exit code 0 (help)."""
        with pytest.raises(SystemExit) as exc_info:
            usage()
        assert exc_info.value.code == 0

    def test_usage_error_message(self):
        """Test usage function with custom error message and exit code 1."""
        with pytest.raises(SystemExit) as exc_info:
            usage("Error: File not found", exitcode=1)
        assert exc_info.value.code == 1

    def test_usage_custom_message(self):
        """Test usage function displays custom message."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.stdout") as mock_stdout:
                usage("Custom error")
        # Exit code should be 0 (default)
        assert exc_info.value.code == 0


class TestMainFunction:
    """Test the main() function with various scenarios."""

    def test_main_with_many_quality_lines(self):
        """Test main() processes multiple quality lines correctly."""
        # Create file with enough quality lines to trigger MAX_QUALITY_LINES_TO_CHECK logic
        lines = []
        for i in range(100):
            lines.append(f"@READ_{i}\n")
            lines.append("ACGTACGTACGTACGTACGTACGTACGT\n")
            lines.append("+\n")
            # Mix of Phred+33 and Phred+64 characters
            if i % 2 == 0:
                lines.append("!" * 28 + "\n")  # Phred+33 unique
            else:
                lines.append("K" * 28 + "\n")  # Ambiguous

        content = "".join(lines)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fastq", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            # Should detect as Phred+33 due to '!' characters
            assert encoding == "33"
        finally:
            os.unlink(temp_file)

    def test_main_only_ambiguous_characters(self):
        """Test main() detects Phred+64 when only ASCII 64+ chars present."""
        # All quality lines contain only ASCII 64+ characters
        content = """@READ_1
ACGTACGTACGTACGTACGTACGTACGT
+
KKKKKKKKKKKKKKKKKKKKKKKKKKKK
@READ_2
ACGTACGTACGTACGTACGTACGTACGT
+
LLLLLLLLLLLLLLLLLLLLLLLLLLLL
@READ_3
ACGTACGTACGTACGTACGTACGTACGT
+
MMMMMMMMMMMMMMMMMMMMMMMMMMMM
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fastq", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            # All chars >= ASCII 64, so detects as Phred+64
            assert encoding == "64"
        finally:
            os.unlink(temp_file)

    def test_main_phred33_early_detection(self):
        """Test main() returns immediately upon finding Phred+33 unique char."""
        # First quality line has Phred+33 unique character
        content = """@READ_1
ACGTACGTACGTACGTACGTACGTACGT
+
!KKKKKKKKKKKKKKKKKKKKKKKKKKK
@READ_2
ACGTACGTACGTACGTACGTACGTACGT
+
KKKKKKKKKKKKKKKKKKKKKKKKKKKK
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fastq", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            # Should return "33" immediately after finding '!'
            assert encoding == "33"
        finally:
            os.unlink(temp_file)

    def test_main_lowest_ascii_determines_phred64(self):
        """Test main() uses lowest ASCII value to determine Phred+64."""
        # All quality characters are ASCII 64+
        content = """@READ_1
ACGTACGTACGTACGTACGTACGTACGT
+
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@READ_2
ACGTACGTACGTACGTACGTACGTACGT
+
BBBBBBBBBBBBBBBBBBBBBBBBBBBB
@READ_3
ACGTACGTACGTACGTACGTACGTACGT
+
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fastq", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            # All characters >= ASCII 64, should be Phred+64
            assert encoding == "64"
        finally:
            os.unlink(temp_file)

    def test_main_empty_quality_lines(self):
        """Test main() handles empty quality lines gracefully."""
        # File with empty quality lines (malformed, but should handle)
        content = """@READ_1
ACGTACGT
+

@READ_2
ACGTACGT
+
AAAAAAAA
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fastq", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            # Second quality line has all ASCII 64+ chars, detects as Phred+64
            assert encoding == "64"
        finally:
            os.unlink(temp_file)

    def test_main_real_world_degraded_quality(self):
        """Test with real-world degraded quality reads (common at read ends)."""
        content = b"""@SRR000001.1/1
TTACCGGAGTAATAAAAGTGCCACAAAAGAGGGTCAGGAACAGGAGACCTTCACCCATTGGAGGTGCACCACTGACCCCCATGTACCCCGTAATGCCGC
+
JJJFFJJFJJFJFJJFFJFFJJFJFFJFFJJJJFJFJJJJJJJFJJFJJFFJJFFJFJFJFJFJFFFFJJFJJJFFJJJFJJJJFJJJJFFFFFFFF
@SRR000002.1/1
AGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAG
+
###!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@SRR000003.1/1
TGTAGGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGAGA
+
9:<;?ACDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~abcdefghijklmnopqrstuvwxyz{|
"""
        with tempfile.NamedTemporaryFile(suffix=".fastq.gz", delete=False) as f:
            with gzip.open(f.name, "wb") as gz:
                gz.write(content)
            temp_file = f.name

        try:
            encoding = main(temp_file)
            # Contains '#' (ASCII 35) which is Phred+33 unique
            assert encoding == "33"
        finally:
            os.unlink(temp_file)


class TestCLI:
    """Test command-line interface functionality."""

    def test_script_execution_with_real_file(self):
        """Test running the script as a command-line tool."""
        import subprocess

        # Create a temporary Phred+33 FastQ file
        content = """@READ_1
ACGTACGTACGTACGTACGTACGTACGT
+
!KKKKKKKKKKKKKKKKKKKKKKKKKKK
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fastq", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            # Run the script as a subprocess
            script_path = (
                Path(__file__).parent.parent
                / "workflow"
                / "scripts"
                / "phred_encoding.py"
            )
            result = subprocess.run(
                ["python", str(script_path), temp_file],
                capture_output=True,
                text=True,
            )
            # Should output "33"
            assert result.stdout.strip() == "33"
            assert result.returncode == 0
        finally:
            os.unlink(temp_file)

    def test_script_with_help_flag(self):
        """Test script help output."""
        import subprocess

        script_path = (
            Path(__file__).parent.parent / "workflow" / "scripts" / "phred_encoding.py"
        )
        result = subprocess.run(
            ["python", str(script_path), "-h"],
            capture_output=True,
            text=True,
        )
        # Help flag should exit with 0 and contain usage info
        assert result.returncode == 0
        assert (
            "usage:" in result.stdout.lower()
            or "Detect Phred encoding" in result.stdout
        )

    def test_script_with_missing_file(self):
        """Test script error handling for missing file."""
        import subprocess

        script_path = (
            Path(__file__).parent.parent / "workflow" / "scripts" / "phred_encoding.py"
        )
        result = subprocess.run(
            ["python", str(script_path), "/nonexistent/file.fastq"],
            capture_output=True,
            text=True,
        )
        # Should exit with non-zero status
        assert result.returncode != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
