from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from typing import Any

from .models import AuditResult, Recommendation


def row_dict(row: AuditResult) -> dict[str, Any]:
    data = asdict(row)
    data["recommendation"] = row.recommendation.value
    return data


def to_json(rows: list[AuditResult]) -> str:
    return json.dumps([row_dict(row) for row in rows], indent=2, ensure_ascii=False) + "\n"


def to_csv(rows: list[AuditResult]) -> str:
    buffer = io.StringIO()
    fieldnames = list(row_dict(rows[0]).keys()) if rows else []
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row_dict(row))
    return buffer.getvalue()


def to_markdown(rows: list[AuditResult]) -> str:
    data = [row_dict(row) for row in rows]
    if not data:
        return ""

    headers = list(data[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in data:
        lines.append("| " + " | ".join(str(row[h]).replace("|", "\\|") for h in headers) + " |")

    return "\n".join(lines) + "\n"


def to_html(rows: list[AuditResult]) -> str:
    data = [row_dict(row) for row in rows]
    if not data:
        return "<!doctype html><html><body><p>No applications found.</p></body></html>\n"

    headers = list(data[0].keys())
    body = ["<!doctype html>", "<html><head><meta charset='utf-8'><title>brew-adoption-audit</title></head><body>"]
    body.append("<h1>brew-adoption-audit report</h1>")
    body.append("<table border='1' cellspacing='0' cellpadding='4'>")
    body.append("<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>")
    for row in data:
        body.append("<tr>" + "".join(f"<td>{str(row[h])}</td>" for h in headers) + "</tr>")
    body.append("</table></body></html>")
    return "\n".join(body) + "\n"


def print_table(rows: list[AuditResult]) -> None:
    data = [row_dict(row) for row in rows]
    headers = [
        "app_name",
        "app_bundle",
        "bundle_id",
        "version",
        "app_store",
        "brew_managed",
        "verified_cask",
        "confidence",
        "recommendation",
    ]

    if not data:
        print("No applications found.")
        return

    widths = {h: min(max(len(h), *(len(str(row[h])) for row in data)), 36) for h in headers}

    def trim(value: Any, width: int) -> str:
        text = str(value)
        return text if len(text) <= width else text[: width - 1] + "…"

    print("  ".join(h.ljust(widths[h]) for h in headers))
    print("  ".join(("-" * widths[h]) for h in headers))

    for row in data:
        print("  ".join(trim(row[h], widths[h]).ljust(widths[h]) for h in headers))

    safe = [row for row in rows if row.recommendation == Recommendation.SAFE_TO_ADOPT]
    manual = [row for row in rows if row.recommendation == Recommendation.MANUAL_REVIEW]

    if safe:
        print("\nSafe-to-adopt candidates — commands are printed only, not executed:")
        for row in safe:
            print(f"  {row.command_preview}    # {row.app_name}")

    if manual:
        print("\nManual review:")
        for row in manual:
            print(f"  {row.app_name}: {row.notes}")
