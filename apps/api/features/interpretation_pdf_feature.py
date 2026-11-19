"""
PDF export of the AI interpretation (`llm_tab.py:925-976`) with reportlab: A4, 2 cm margins, `Section` headers
(Heading2, `#2c4a6e`, spaceAfter 6) and `Body` lines (Normal, spaceAfter 8, leading 14), `Spacer(1, 6)` for empty
lines. Known Tkinter Behaviour Kept 20: any line starting with `##` or `1.` ... `7.` is a header (numbered list items
and `1.5 ...` included; `10.` does not match `1.`).
Label fix L6: headers are XML-escaped like body lines, so `&` or `<` cannot break reportlab or inject markup.
"""

import asyncio
from io import BytesIO
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from errors.llm_errors import EmptyInterpretationError

HEADER_COLOUR = "#2c4a6e"


class InterpretationPdfFeature:
    """Writes the interpretation text as a PDF."""

    async def export(self, text: str) -> bytes:
        """Build the PDF in a worker thread (see `export_bytes`)."""
        return await asyncio.to_thread(self.export_bytes, text)

    def is_header(self, stripped: str) -> bool:
        """The legacy header rule (`llm_tab.py:869-871, 958-961`)."""
        return stripped.startswith("##") or any(stripped.startswith(f"{i}.") for i in range(1, 8))

    def escape(self, text: str) -> str:
        """Escape `&` and `<` (body lines as legacy; headers too, L6)."""
        return text.replace("&", "&amp;").replace("<", "&lt;")

    def export_bytes(self, text: str) -> bytes:
        """
        Build the PDF.

        Args:
            text: Interpretation text

        Returns:
            bytes: The PDF

        Raises:
            EmptyInterpretationError: When the text is empty
        """
        if not text:
            raise EmptyInterpretationError("empty interpretation")
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm
        )
        styles = getSampleStyleSheet()
        h_style = ParagraphStyle(
            "Section", parent=styles["Heading2"], textColor=colors.HexColor(HEADER_COLOUR), spaceAfter=6
        )
        b_style = ParagraphStyle("Body", parent=styles["Normal"], spaceAfter=8, leading=14)
        story: List = []
        for line in text.splitlines():
            stripped = line.strip()
            clean = stripped.lstrip("#").strip()
            if not clean:
                story.append(Spacer(1, 6))
            elif self.is_header(stripped):
                story.append(Paragraph(self.escape(clean), h_style))
            else:
                story.append(Paragraph(self.escape(line), b_style))
        doc.build(story)
        return buffer.getvalue()


interpretation_pdf_feature = InterpretationPdfFeature()
