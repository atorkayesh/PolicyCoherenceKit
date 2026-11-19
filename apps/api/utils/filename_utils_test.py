"""
Unit tests for FilenameBuilder (label fix L10).

Tests cover:
- The legacy `{project}_coherence.xlsx` name with spaces replaced
- Invalid file-name characters and control characters replaced
- The ASCII fallback and the RFC 5987 `filename*` parameter
"""

import unittest

import pytest

from utils.filename_utils import FilenameBuilder


@pytest.mark.unit
class TestFilenameBuilder(unittest.TestCase):
    """Test cases for FilenameBuilder."""

    def setUp(self):
        """Create the builder."""
        self.builder = FilenameBuilder()

    def test_legacy_name_with_spaces(self):
        """Test spaces become underscores as in the legacy export."""
        self.assertEqual(self.builder.xlsx_export_name("WEF Nexus Example"), "WEF_Nexus_Example_coherence.xlsx")

    def test_invalid_characters_replaced(self):
        """Test every invalid character and control character becomes `_`."""
        name = self.builder.xlsx_export_name('a/b\\c:d*e?f"g<h>i|j\x01k\x7f')
        self.assertEqual(name, "a_b_c_d_e_f_g_h_i_j_k__coherence.xlsx")

    def test_ascii_header(self):
        """Test an ASCII name appears unchanged in both parameters."""
        header = self.builder.content_disposition("Plan_coherence.xlsx")
        self.assertEqual(header, "attachment; filename=\"Plan_coherence.xlsx\"; filename*=UTF-8''Plan_coherence.xlsx")

    def test_non_ascii_header(self):
        """Test non-ASCII characters get an `_` fallback and a percent-encoded `filename*`."""
        header = self.builder.content_disposition("Jülich_Größe.xlsx")
        self.assertEqual(
            header,
            "attachment; filename=\"J_lich_Gr__e.xlsx\"; filename*=UTF-8''J%C3%BClich_Gr%C3%B6%C3%9Fe.xlsx",
        )
