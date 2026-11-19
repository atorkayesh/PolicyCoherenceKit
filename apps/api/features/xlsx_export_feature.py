"""
XLSX export of the current run (`app.py:3085-3217`; Settled Decision 8: no run history).

Sheets: one per decision-maker (rating fills and font colours), then Aggregated, Coh Scores, Range Influence and
Centrality (sorted by betweenness, descending, stable). Numbers are written as computed (`-0.0` included). Titles
follow L3 and every text cell is a string (L15).
"""

import asyncio
from io import BytesIO
from typing import List, Optional, Tuple

from openpyxl import Workbook
from openpyxl.styles import Alignment

from constants.export_constants import XLSX_STYLE, XLSX_TEXT
from constants.rating_constants import RATING_FILLS, RATING_TEXT_COLOURS
from features.analysis_feature import AnalysisFeature, AnalysisOutput, analysis_feature
from models.analysis_request_models import AnalysisRequest
from utils.aggregation_label_utils import aggregation_labeler
from utils.excel_style_utils import ExcelStyler, excel_styler
from utils.filename_utils import filename_builder
from utils.sheet_title_utils import sheet_title_builder


class XlsxExportFeature:
    """Builds the workbook."""

    def __init__(self, analysis: Optional[AnalysisFeature] = None, styler: Optional[ExcelStyler] = None):
        """
        Create the feature.

        Args:
            analysis: Analysis feature; defaults to the shared instance
            styler: Cell styling; defaults to the shared instance
        """
        self._analysis = analysis or analysis_feature
        self._styler = styler or excel_styler

    async def export(self, request: AnalysisRequest) -> Tuple[bytes, str]:
        """
        Export the analysis in a worker thread.

        Args:
            request: Validated analysis request (every tie resolved)

        Returns:
            Tuple[bytes, str]: Workbook bytes and the download name (L10)
        """
        content = await asyncio.to_thread(self.export_bytes, request)
        return content, filename_builder.xlsx_export_name(request.project_name)

    def export_bytes(self, request: AnalysisRequest) -> bytes:
        """
        Build the workbook.

        Args:
            request: Validated analysis request

        Returns:
            bytes: The `.xlsx` file
        """
        output = self._analysis.compute(request)
        result = output.run.result
        result_titles = sheet_title_builder.result_titles(
            aggregation_labeler.sheet_label(aggregation_labeler.method_label(result))
        )
        names = [m.decision_maker for m in output.run.matrices]
        wb = Workbook()
        wb.remove(wb.active)
        for title, matrix in zip(
            sheet_title_builder.decision_maker_titles(names, result_titles), output.run.matrices, strict=True
        ):
            ws = wb.create_sheet(title=title)
            self._frame(ws, matrix.codes, matrix.policies)
            for i in range(len(matrix.codes)):
                for j in range(len(matrix.codes)):
                    value = matrix.get_rating(i, j)
                    cell = self._matrix_cell(ws, i, j, value)
                    if value in RATING_FILLS:
                        cell.fill = self._styler.fill(RATING_FILLS[value])
                        cell.font = self._styler.font(RATING_TEXT_COLOURS[value])
            self._styler.auto_width(ws)
        self._results(wb, result_titles, output)
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    def _results(self, wb: Workbook, titles: List[str], output: AnalysisOutput) -> None:
        """The four result sheets."""
        result = output.run.result
        ws = wb.create_sheet(title=titles[0])
        self._frame(ws, result.codes, result.policies)
        for i in range(result.n):
            for j in range(result.n):
                cell = self._matrix_cell(ws, i, j, result.scores.get((i, j), 0.0) or 0.0)
                cell.number_format = XLSX_STYLE["SCORE_NUMBER_FORMAT"]
        self._styler.auto_width(ws)
        tables = [
            (titles[1], XLSX_TEXT["SCORES_HEADER"], output.scores, ("code", "policy", "oi", "ii", "woi", "wii")),
            (titles[2], XLSX_TEXT["ENTROPY_HEADER"], output.entropy, ("code", "policy", "entropy", "category")),
            (
                titles[3],
                XLSX_TEXT["CENTRALITY_HEADER"],
                sorted(output.centrality, key=lambda x: x["betweenness"], reverse=True),
                ("code", "policy", "betweenness", "closeness"),
            ),
        ]
        for title, header, rows, keys in tables:
            ws = wb.create_sheet(title=title)
            for c, h in enumerate(header, 1):
                self._styler.header(ws, 1, c, h)
            for r, row in enumerate(rows, 2):
                for c, key in enumerate(keys, 1):
                    self._styler.cell(ws, r, c, row[key])
            self._styler.auto_width(ws)

    def _frame(self, ws, codes: List[str], policies: List[str]) -> None:
        """Policy index row, corner label, and the code headers of a matrix sheet."""
        styler = self._styler
        styler.cell(ws, 1, 1, XLSX_TEXT["POLICY_INDEX"]).font = styler.font(bold=True)
        for k, (code, name) in enumerate(zip(codes, policies, strict=True)):
            styler.cell(ws, 1, k + 2, f"{code}: {name}")
        styler.cell(ws, 3, 1, XLSX_TEXT["CORNER"]).font = styler.font(bold=True, italic=True)
        for j, code in enumerate(codes):
            styler.header(ws, 3, j + 2, code)
        for i, code in enumerate(codes):
            styler.header(ws, i + 4, 1, code)

    def _matrix_cell(self, ws, i: int, j: int, value):
        cell = self._styler.cell(ws, i + 4, j + 2, value)
        cell.alignment = Alignment(horizontal="center")
        cell.border = self._styler.border
        return cell


xlsx_export_feature = XlsxExportFeature()
