"""Functions for exporting structured data to CSV and Excel files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


_FORMULA_TRIGGER_REPLACEMENTS = {
    "=": "＝",
    "+": "＋",
    "-": "－",
    "@": "＠",
}

_MIN_COLUMN_WIDTH = 10.0
_MAX_COLUMN_WIDTH = 45.0
_WRAP_COLUMN_WIDTH = 38.0
_WRAP_THRESHOLD = 45
_NUMERIC_COLUMN_MAX_WIDTH = 20.0

_HEADER_FONT = Font(bold=True, color="1F3864")
_HEADER_FILL = PatternFill("solid", fgColor="DDEBF7")
_HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center", wrap_text=False)
_HEADER_BORDER = Border(bottom=Side(style="thin", color="8EA9DB"))

_SUMMARY_LABEL_FONT = Font(bold=True)


def _sanitize_cell_value(value: object) -> object:
    """Prevent spreadsheet formula injection by neutralising formula-like values.

    A leading formula trigger such as ``=`` is replaced with a visually identical
    full-width character. Spreadsheet applications then treat the cell as text,
    while the original formula text no longer appears in the exported file.
    """
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return trimmed

        first = trimmed[0]
        replacement = _FORMULA_TRIGGER_REPLACEMENTS.get(first)
        if replacement is not None:
            return replacement + trimmed[1:]

        if first in {"\t", "\r", "\n"}:
            return "'" + trimmed

        return trimmed
    return value


def _display_length(value: object) -> int:
    """Return the number of characters a value occupies in a spreadsheet cell."""
    if value is None:
        return 0
    if isinstance(value, bool):
        return len(str(value))
    if isinstance(value, (int, float)):
        return len(f"{value:g}")
    return len(str(value))


def _is_numeric_column(values: list[object]) -> bool:
    """Return True when every populated value in the column is a real number."""
    populated = False
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        populated = True
    return populated


def _plan_column_widths(headers: list[object], frame: pd.DataFrame) -> list[tuple[float, bool]]:
    """Return the display width and wrapping flag for each column.

    Widths follow the actual content of each column so that short columns stay
    compact and long text or URLs are wrapped inside a bounded width instead of
    forcing a very wide sheet.
    """
    plan: list[tuple[float, bool]] = []

    for index, header in enumerate(headers):
        values = list(frame.iloc[:, index]) if index < len(frame.columns) else []
        longest = _display_length(header)
        for value in values:
            longest = max(longest, _display_length(value))

        if _is_numeric_column(values):
            plan.append((max(_MIN_COLUMN_WIDTH, min(longest + 2, _NUMERIC_COLUMN_MAX_WIDTH)), False))
        elif longest <= _WRAP_THRESHOLD:
            plan.append((max(_MIN_COLUMN_WIDTH, min(longest + 2, _MAX_COLUMN_WIDTH)), False))
        else:
            plan.append((_WRAP_COLUMN_WIDTH, True))

    return plan


def _format_data_sheet(data_sheet, headers: list[object], frame: pd.DataFrame) -> None:
    """Apply readable formatting to the Data worksheet."""
    plan = _plan_column_widths(headers, frame)

    for index, (width, wrap) in enumerate(plan):
        letter = get_column_letter(index + 1)
        data_sheet.column_dimensions[letter].width = width

        for row_index in range(2, data_sheet.max_row + 1):
            cell = data_sheet.cell(row=row_index, column=index + 1)
            numeric = isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool)
            cell.alignment = Alignment(
                horizontal="right" if numeric else "left",
                vertical="top" if wrap else "center",
                wrap_text=wrap,
            )

    for cell in data_sheet[1]:
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = _HEADER_ALIGNMENT
        cell.border = _HEADER_BORDER

    data_sheet.freeze_panes = "A2"
    data_sheet.auto_filter.ref = data_sheet.dimensions
    data_sheet.row_dimensions[1].height = 20


def _format_summary_sheet(summary_sheet, summary_stats: dict[str, object]) -> None:
    """Keep the Summary worksheet readable without altering its content."""
    for index, (key, value) in enumerate(summary_stats.items(), start=1):
        label_cell = summary_sheet.cell(row=index, column=1, value=key)
        value_cell = summary_sheet.cell(row=index, column=2, value=value)
        label_cell.font = _SUMMARY_LABEL_FONT
        label_cell.alignment = Alignment(horizontal="left", vertical="center")
        value_cell.alignment = Alignment(horizontal="left", vertical="center")

    label_width = max((_display_length(key) for key in summary_stats), default=_MIN_COLUMN_WIDTH)
    value_width = max((_display_length(value) for value in summary_stats.values()), default=_MIN_COLUMN_WIDTH)
    summary_sheet.column_dimensions["A"].width = max(_MIN_COLUMN_WIDTH, min(label_width + 2, _MAX_COLUMN_WIDTH))
    summary_sheet.column_dimensions["B"].width = max(_MIN_COLUMN_WIDTH, min(value_width + 2, _MAX_COLUMN_WIDTH))
    summary_sheet.freeze_panes = "A2"


def export_csv(records: list[dict], output_path: str | Path) -> Path:
    """Write a list of dictionaries to a CSV file and return the resulting path.

    The file is written as UTF-8 with a byte order mark so that spreadsheet
    applications detect the encoding instead of assuming the system code page.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not records:
        path.write_text("", encoding="utf-8")
        return path

    frame = pd.DataFrame(records)
    safe_frame = frame.map(_sanitize_cell_value)
    safe_frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def export_excel(
    records: list[dict],
    output_path: str | Path,
    summary_stats: dict[str, object] | None = None,
    sheet_name: str = "Data",
) -> Path:
    """Write a list of dictionaries to an Excel workbook and return the resulting path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    data_sheet = workbook.active
    data_sheet.title = sheet_name

    if not records:
        data_sheet.append(["No data available"])
        if summary_stats:
            summary_sheet = workbook.create_sheet("Summary")
            for index, (key, value) in enumerate(summary_stats.items(), start=1):
                summary_sheet.cell(row=index, column=1, value=key)
                summary_sheet.cell(row=index, column=2, value=value)
        workbook.save(path)
        return path

    frame = pd.DataFrame(records)
    frame = frame.map(_sanitize_cell_value)

    headers = list(frame.columns)
    data_sheet.append(headers)
    for row in frame.itertuples(index=False, name=None):
        data_sheet.append(list(row))

    _format_data_sheet(data_sheet, headers, frame)

    if summary_stats:
        summary_sheet = workbook.create_sheet("Summary")
        for index, (key, value) in enumerate(summary_stats.items(), start=1):
            summary_sheet.cell(row=index, column=1, value=key)
            summary_sheet.cell(row=index, column=2, value=value)
        _format_summary_sheet(summary_sheet, summary_stats)

    workbook.save(path)
    return path
