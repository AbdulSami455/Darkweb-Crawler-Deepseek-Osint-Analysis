#!/usr/bin/env python3
"""
PDF reporting utilities for OSINT analysis results.
"""

import os
import io
import json
import base64
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch


def _safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    try:
        return d.get(key, default)
    except Exception:
        return default


def build_report_filename(result: Dict[str, Any]) -> str:
    url = _safe_get(_safe_get(result, "metadata", {}), "url", "site") or "site"
    safe_url = (
        str(url).replace("http://", "").replace("https://", "").split("/")[0]
    )
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"osint_report_{safe_url}_{ts}.pdf"


def _default_output_dir(result: Dict[str, Any]) -> Path:
    # Try to place next to torcrawl/output/<domain>
    url = _safe_get(_safe_get(result, "metadata", {}), "url", "") or ""
    domain = (
        str(url).replace("http://", "").replace("https://", "").split("/")[0]
        if url
        else "report"
    )
    here = Path(__file__).resolve().parent.parent / "torcrawl" / "output" / domain
    here.mkdir(parents=True, exist_ok=True)
    return here


def encode_pdf_base64(pdf_path: str) -> str:
    data = Path(pdf_path).read_bytes()
    return base64.b64encode(data).decode("ascii")


def _para(text: str, style_name: str = "Normal") -> Paragraph:
    styles = getSampleStyleSheet()
    return Paragraph(text.replace("\n", "<br/>"), styles[style_name])


def _to_table(data: Dict[str, Any]) -> Table:
    rows = [("Key", "Value")]
    for k, v in data.items():
        if isinstance(v, (dict, list)):
            v_str = json.dumps(v, indent=2, ensure_ascii=False)
        else:
            v_str = str(v)
        rows.append((str(k), v_str))
    table = Table(rows, colWidths=[2.2 * inch, 4.6 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efefef")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#333333")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def generate_pdf_report(
    analysis_result: Dict[str, Any], output_dir: Optional[str] = None, filename: Optional[str] = None
) -> str:
    out_dir_path = Path(output_dir) if output_dir else _default_output_dir(analysis_result)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    pdf_name = filename or build_report_filename(analysis_result)
    pdf_path = out_dir_path / pdf_name

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, title="Dark Web OSINT Report")
    story = []

    # Header
    story.append(_para("<b>Dark Web OSINT Report</b>", "Title"))
    story.append(Spacer(1, 0.2 * inch))

    # Metadata
    metadata = _safe_get(analysis_result, "metadata", {}) or {}
    meta_view = {
        "URL": metadata.get("url"),
        "Depth": metadata.get("depth"),
        "Started At": metadata.get("started_at"),
        "LangChain": metadata.get("use_langchain"),
        "Connectivity Warning": metadata.get("connectivity_warning"),
        "Model": _safe_get(analysis_result, "model"),
        "Tokens Used": _safe_get(analysis_result, "tokens_used"),
        "Analysis Method": _safe_get(analysis_result, "analysis_method", "traditional_json"),
    }
    story.append(_para("<b>Metadata</b>", "Heading2"))
    story.append(_to_table({k: v for k, v in meta_view.items() if v is not None}))
    story.append(Spacer(1, 0.15 * inch))

    # Analysis section
    story.append(_para("<b>Analysis</b>", "Heading2"))
    analysis = _safe_get(analysis_result, "analysis")
    if isinstance(analysis, dict):
        # If structured dict (from LangChain or parsed JSON)
        story.append(_to_table(analysis))
    else:
        # Fallback: raw text
        story.append(_para(str(analysis or "No analysis available.")))
    story.append(Spacer(1, 0.15 * inch))

    # Errors
    if _safe_get(analysis_result, "error") or _safe_get(analysis_result, "details"):
        story.append(_para("<b>Errors / Details</b>", "Heading2"))
        err_block = {
            "error": _safe_get(analysis_result, "error"),
            "details": _safe_get(analysis_result, "details"),
        }
        story.append(_to_table({k: v for k, v in err_block.items() if v}))

    doc.build(story)
    return str(pdf_path)


