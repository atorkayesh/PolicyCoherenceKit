"""
Unit tests for InterpretationPdfFeature.

Tests cover:
- The legacy header rule (`##`, `1.` ... `7.`; `10.` is not a header, `1.5` is) and empty-line spacers
- Header escaping (L6): `&` and `<` in headers no longer break reportlab; an `<img>` header renders as text
- Empty text is rejected
"""

import unittest
from unittest.mock import patch

import pytest
from reportlab.platypus import Paragraph

from errors.llm_errors import EmptyInterpretationError
from features.interpretation_pdf_feature import InterpretationPdfFeature


@pytest.mark.unit
class TestInterpretationPdfFeature(unittest.TestCase):
    """Test cases for InterpretationPdfFeature."""

    def setUp(self):
        """Create the feature."""
        self.feature = InterpretationPdfFeature()

    def test_header_rule(self):
        """Test the legacy header rule verbatim (`startswith(f"{i}.")` for i in 1..7)."""
        for line, header in [
            ("## Title", True),
            ("1. Overall", True),
            ("7. Last", True),
            ("10. Item", False),
            ("1.5 percent", True),
            ("8. Eight", False),
            ("Body", False),
        ]:
            with self.subTest(line=line):
                self.assertEqual(self.feature.is_header(line), header)

    def test_headers_are_escaped(self):
        """Test a header with `&` and markup builds and is passed as escaped text."""
        text = '## <img src="http://127.0.0.1/"> R&D\n\nBody & <b>text</b>'
        with patch("features.interpretation_pdf_feature.Paragraph", wraps=Paragraph) as paragraph:
            pdf = self.feature.export_bytes(text)
        self.assertTrue(pdf.startswith(b"%PDF"))
        texts = [call.args[0] for call in paragraph.call_args_list]
        self.assertEqual(texts[0], '&lt;img src="http://127.0.0.1/"> R&amp;D')
        self.assertEqual(texts[1], "Body &amp; &lt;b>text&lt;/b>")

    def test_empty_text(self):
        """Test empty text raises the legacy message."""
        with self.assertRaises(EmptyInterpretationError) as context:
            self.feature.export_bytes("")
        self.assertEqual(context.exception.public_message, "Generate an interpretation first.")
