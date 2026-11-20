import argparse
import os
import json
import sys
import time
from html import escape
from io import BytesIO
from pathlib import Path


def _ensure_bundled_python_runtime(required_modules):
    missing = []
    for module_name in required_modules:
        try:
            __import__(module_name)
        except ModuleNotFoundError:
            missing.append(module_name)
    if not missing:
        return

    bundled_python = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
    if bundled_python.is_file() and Path(sys.executable).resolve() != bundled_python.resolve():
        os.execv(str(bundled_python), [str(bundled_python), __file__, *sys.argv[1:]])


_ensure_bundled_python_runtime(("PIL", "reportlab"))

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


STATUS_COLOR = {
    "pass": colors.HexColor("#1f7a1f"),
    "passed": colors.HexColor("#1f7a1f"),
    "failed": colors.HexColor("#b42318"),
    "fail": colors.HexColor("#b42318"),
    "warning": colors.HexColor("#b54708"),
    "warn": colors.HexColor("#b54708"),
    "skipped": colors.HexColor("#667085"),
    "skip": colors.HexColor("#667085"),
    "info": colors.HexColor("#175cd3"),
}


PURPOSE_LABEL = {
    "code": "Code Validation",
    "ui": "UI Validation",
    "image": "Image Review",
    "api": "API Validation",
    "document": "Document Validation",
    "mixed": "Mixed Validation",
}


DEFAULT_RETENTION_DAYS = 7
REPORT_EXTENSIONS = {".pdf"}
FULL_TABLE_WIDTH = 7.25 * inch
LABEL_COLUMN_WIDTH = 1.45 * inch
CONTENT_COLUMN_WIDTH = FULL_TABLE_WIDTH - LABEL_COLUMN_WIDTH
INPUT_INLINE_IMAGE_MAX_WIDTH = 1.65 * inch
INPUT_INLINE_IMAGE_MAX_HEIGHT = 1.3 * inch
COMPARISON_INLINE_IMAGE_MAX_WIDTH = 2.45 * inch
COMPARISON_INLINE_IMAGE_MAX_HEIGHT = 1.85 * inch
FULL_DETAIL_MODES = {"full", "detailed", "verbose"}
USED_FIELD_NAMES = ("used", "method", "tool", "command", "executed_command", "workflow", "script", "route", "endpoint")
PASS_REASON_FIELD_NAMES = ("pass_reason", "why_passed", "why_pass", "acceptance_reason", "pass_criteria_result")
PASS_STATUS_VALUES = {"pass", "passed"}
BARE_PASS_OUTPUT_VALUES = {"ok", "okay", "pass", "passed", "done", "works", "success", "successful", "fixed"}


def _status_text(value): return str(value or "info").strip().lower()


def _status_color(value): return STATUS_COLOR.get(_status_text(value), colors.HexColor("#175cd3"))


def _purpose_category(value): return str(value or "mixed").strip().lower()


def _stringify(value):
    if value is None: return ""
    if isinstance(value, (list, tuple)): return ", ".join(_stringify(item) for item in value)
    return str(value)


def _label_text(value): return _stringify(value).replace("_", " ").strip().title()


def _pairs(value):
    if isinstance(value, dict): return [(str(key), _stringify(raw_value)) for key, raw_value in value.items()]
    if not isinstance(value, list): return []
    rows = []
    for item in value:
        if isinstance(item, dict) and "label" in item: rows.append((str(item["label"]), _stringify(item.get("value", ""))))
        elif isinstance(item, (list, tuple)) and len(item) >= 2: rows.append((_stringify(item[0]), _stringify(item[1])))
    return rows


def _first_present_value(case, case_details, field_names):
    for field_name in field_names:
        value = case.get(field_name)
        if value:
            return value
    for field_name in field_names:
        value = case_details.pop(field_name, "")
        if value:
            return value
    return ""


def _field_value(case, case_details, field_names):
    for container in (case, case_details):
        for field_name in field_names:
            value = container.get(field_name)
            if value:
                return _stringify(value)
    return ""


def _comparison_container(case):
    return case.get("comparison") if isinstance(case.get("comparison"), dict) else {}


def _artifact_paths(case):
    artifacts = case.get("artifacts") or case.get("images") or []
    paths = []
    for artifact in artifacts:
        if isinstance(artifact, dict) and artifact.get("path"):
            paths.append(_stringify(artifact["path"]))
    return paths


def _bare_pass_output(value):
    return _stringify(value).strip().lower().strip(".! ") in BARE_PASS_OUTPUT_VALUES


def _case_evidence_values(case):
    case_details = dict(case.get("details") or {})
    comparison = _comparison_container(case)
    input_value = (
        _field_value(case, case_details, ("request", "sample_request", "request_example", "request_payload", "example_input", "input", "objective", "input_image_path", "input_image"))
        or _field_value(comparison, {}, ("before", "before_data", "baseline", "original", "before_image_path", "before_image", "baseline_image_path", "original_image_path"))
    )
    if not input_value and case.get("steps"):
        input_value = " | ".join(_stringify(step) for step in case["steps"])
    output_value = (
        _field_value(case, case_details, ("response", "sample_response", "response_example", "response_payload", "sample_output", "sample_log_excerpt", "log_excerpt", "example_output", "output", "result"))
        or _field_value(comparison, {}, ("after", "after_data", "current", "revised", "after_image_path", "after_image", "current_image_path", "revised_image_path"))
    )
    if not output_value:
        output_value = ", ".join(_artifact_paths(case))
    return {
        "input": input_value,
        "used": _field_value(case, case_details, USED_FIELD_NAMES),
        "output": output_value,
        "pass_reason": _field_value(case, case_details, PASS_REASON_FIELD_NAMES),
    }


def _validate_evidence_contract(test_cases):
    failures = []
    for index, case in enumerate(test_cases, start=1):
        if _status_text(case.get("status")) not in PASS_STATUS_VALUES:
            continue
        evidence = _case_evidence_values(case)
        missing = [label for label, value in evidence.items() if not value]
        if evidence["output"] and _bare_pass_output(evidence["output"]):
            missing.append("output must be real evidence, not a bare status word")
        if missing:
            failures.append(f"case {index} ({case.get('name', 'Unnamed test')}): missing {', '.join(missing)}")
    if failures:
        raise ValueError("Passing report cases must include real Input, Used, Output, and Why Pass evidence:\n" + "\n".join(failures))


def _paragraph(text, style): return Paragraph(escape(_stringify(text)).replace("\n", "<br/>"), style)


def _bullet_lines(values): return "<br/>".join(f"• {escape(_stringify(value))}" for value in values if _stringify(value))


def _compact_inline_pairs(pairs):
    compact_parts = []
    for label, raw_value in pairs:
        value = _stringify(raw_value).replace("\n", " ").strip()
        if not value: continue
        compact_parts.append(f"{_label_text(label)}: {value}")
    return " | ".join(compact_parts)


def _compact_context(environment_pairs, generated_at):
    compact_parts = []
    for label, raw_value in environment_pairs:
        key = _stringify(label).strip().lower()
        value = _stringify(raw_value).replace("\n", " ").strip()
        if not value: continue
        if key == "workspace":
            compact_parts.append(f"Workspace: {Path(value).name or value}")
            continue
        if key == "changed_files":
            changed_files = [item.strip() for item in value.split(",") if item.strip()]
            compact_parts.append(f"Changed Files: {len(changed_files)}")
            continue
        compact_parts.append(f"{_label_text(label)}: {value}")
    if generated_at: compact_parts.append(f"Generated: {generated_at}")
    return " | ".join(compact_parts[:5])


def _fit_header_style(base_style, text, normal_size, compact_size, tight_size):
    text_length = len(_stringify(text))
    if text_length > 58: return ParagraphStyle(name=f"{base_style.name}Tight", parent=base_style, fontSize=tight_size, leading=tight_size + 3)
    if text_length > 40: return ParagraphStyle(name=f"{base_style.name}Compact", parent=base_style, fontSize=compact_size, leading=compact_size + 3)
    return ParagraphStyle(name=f"{base_style.name}Normal", parent=base_style, fontSize=normal_size, leading=normal_size + 4)


def _scaled_image(path, width_limit, height_limit, h_align="LEFT"):
    image_width, image_height = ImageReader(str(path)).getSize()
    scale = min(width_limit / image_width, height_limit / image_height, 1)
    flowable = Image(str(path), width=image_width * scale, height=image_height * scale)
    flowable.hAlign = h_align
    return flowable


def _full_width_artifact_images(path, width_limit, height_limit):
    image_width, image_height = ImageReader(str(path)).getSize()
    scale = min(width_limit / image_width, 1)
    if image_height * scale <= height_limit:
        flowable = Image(str(path), width=image_width * scale, height=image_height * scale)
        flowable.hAlign = "LEFT"
        return [flowable]

    slice_height = max(1, int(height_limit / scale))
    image = PILImage.open(path).convert("RGB")
    flowables = []
    for top in range(0, image_height, slice_height):
        cropped_image = image.crop((0, top, image_width, min(image_height, top + slice_height)))
        image_buffer = BytesIO()
        cropped_image.save(image_buffer, format="PNG")
        image_buffer.seek(0)
        flowable = Image(image_buffer, width=image_width * scale, height=cropped_image.height * scale)
        flowable.hAlign = "LEFT"
        flowable._codex_image_buffer = image_buffer
        flowables.append(flowable)
    return flowables


def _value_cell_value(text, image_path, styles, missing_label="input image", width_limit=INPUT_INLINE_IMAGE_MAX_WIDTH, height_limit=INPUT_INLINE_IMAGE_MAX_HEIGHT):
    flowables = []
    if text:
        flowables.append(_paragraph(text, styles["TableText"]))
    if not image_path:
        if flowables: return flowables[0]
        return _paragraph(f"Missing {missing_label}.", styles["Missing"])
    image_path = Path(image_path).expanduser()
    if flowables: flowables.append(Spacer(1, 0.04 * inch))
    if image_path.exists():
        flowables.append(_scaled_image(image_path, width_limit, height_limit))
    else:
        flowables.append(_paragraph(f"Missing {missing_label}: {image_path}", styles["Missing"]))
    if len(flowables) == 1: return flowables[0]
    return flowables


def _input_cell_value(text, image_path, styles):
    return _value_cell_value(text, image_path, styles, missing_label="input image")


def _show_case_details(manifest, case):
    detail_mode = _stringify(manifest.get("case_detail_mode", "compact")).strip().lower()
    if detail_mode in FULL_DETAIL_MODES:
        return True
    return bool(case.get("show_details"))


def _comparison_enabled(manifest, case):
    if bool(manifest.get("comparison_mode") or case.get("comparison_mode")):
        return True
    return bool(case.get("comparison") or case.get("before") or case.get("after") or case.get("before_data") or case.get("after_data") or case.get("before_image_path") or case.get("after_image_path"))


def _comparison_value(case, case_details, field_name):
    comparison = case.get("comparison") if isinstance(case.get("comparison"), dict) else {}
    field_names = {
        "before": ["before", "before_data", "baseline", "original"],
        "after": ["after", "after_data", "current", "revised"],
        "before_image_path": ["before_image_path", "before_image", "baseline_image_path", "original_image_path"],
        "after_image_path": ["after_image_path", "after_image", "current_image_path", "revised_image_path"],
        "summary": ["summary", "comparison_summary", "change_summary", "diff"]
    }.get(field_name, [field_name])
    for current_field_name in field_names:
        current_value = comparison.get(current_field_name) or case.get(current_field_name) or case_details.pop(current_field_name, "")
        if current_value:
            return current_value
    return ""


def _meta_banner(text, styles):
    banner_table = Table([[Paragraph(text, styles["MetaBannerText"])]], colWidths=[FULL_TABLE_WIDTH], rowHeights=[0.42 * inch], hAlign="LEFT")
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#344054")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return banner_table


def _resolve_cleanup_root(output_path, cleanup_root):
    if cleanup_root: return Path(cleanup_root).expanduser().resolve()
    for parent in (output_path.parent, *output_path.parents):
        if parent.name == "verify-skill": return parent
    return None


def _last_activity_timestamp(path):
    # Access time is not reliable enough across filesystems for cache pruning.
    # Use last modified time so 7-day cleanup stays deterministic.
    return path.stat().st_mtime


def cleanup_old_reports(cleanup_root, retention_days=DEFAULT_RETENTION_DAYS, keep_paths=None):
    if not cleanup_root or retention_days <= 0 or not cleanup_root.exists(): return []
    cutoff_timestamp = time.time() - (retention_days * 24 * 60 * 60)
    keep_paths = {Path(path).expanduser().resolve() for path in (keep_paths or [])}
    deleted_paths = []
    for path in sorted(cleanup_root.rglob("*")):
        if path.is_dir() or path.suffix.lower() not in REPORT_EXTENSIONS: continue
        resolved_path = path.resolve()
        if resolved_path in keep_paths or _last_activity_timestamp(resolved_path) >= cutoff_timestamp: continue
        resolved_path.unlink()
        deleted_paths.append(resolved_path)
    return deleted_paths


def _table(rows, column_widths, has_header=True):
    table = Table(rows, colWidths=column_widths, hAlign="LEFT", splitByRow=1)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d5dd")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if has_header:
        style.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f4f7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#101828")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fcfcfd")]),
        ])
    else:
        style.append(("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#fcfcfd")]))
    table.setStyle(TableStyle(style))
    return table


def _artifact_blocks(artifacts, styles, width_limit=FULL_TABLE_WIDTH, height_limit=8.15 * inch, spacer_height=0.14 * inch, section_title=""):
    blocks = []
    for artifact_index, artifact in enumerate(artifacts):
        label = artifact.get("label", "Artifact")
        path = Path(artifact.get("path", "")).expanduser() if artifact.get("path") else None
        caption = artifact.get("caption", "")
        title_blocks = []
        if section_title and artifact_index == 0:
            title_blocks.append(_paragraph(section_title, styles["SectionTitle"]))
        title_blocks.append(_paragraph(f"{label}", styles["ArtifactTitle"]))
        if path and path.exists():
            fit_mode = _stringify(artifact.get("fit_mode") or artifact.get("image_fit")).strip().lower()
            if artifact.get("preserve_full_image") or fit_mode in {"contain", "fit", "fit_page", "full"}:
                image_blocks = [_scaled_image(path, width_limit, height_limit, "CENTER")]
            else:
                image_blocks = _full_width_artifact_images(path, width_limit, height_limit)
            blocks.append(KeepTogether(title_blocks + [image_blocks[0]]))
            blocks.extend(image_blocks[1:])
        elif path:
            blocks.extend(title_blocks)
            blocks.append(_paragraph(f"Missing artifact: {path}", styles["Missing"]))
        else:
            blocks.extend(title_blocks)
            blocks.append(_paragraph("Missing artifact path", styles["Missing"]))
        if caption: blocks.append(_paragraph(caption, styles["Caption"]))
        blocks.append(Spacer(1, spacer_height))
    return blocks

def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontSize=22, leading=26, alignment=1, spaceAfter=8))
    styles.add(ParagraphStyle(name="ReportSubtitle", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=14, leading=17, alignment=1, textColor=colors.HexColor("#101828"), spaceAfter=10))
    styles.add(ParagraphStyle(name="MetaBannerText", parent=styles["BodyText"], alignment=1, fontSize=9.2, leading=11, textColor=colors.white, spaceAfter=0))
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], fontSize=15.5, leading=18, textColor=colors.HexColor("#101828"), spaceBefore=8, spaceAfter=6))
    styles.add(ParagraphStyle(name="CaseHeader", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=11.25, leading=13.2, textColor=colors.HexColor("#101828"), spaceAfter=0))
    styles.add(ParagraphStyle(name="TableText", parent=styles["BodyText"], fontSize=8.6, leading=10.1, spaceAfter=0))
    styles.add(ParagraphStyle(name="Caption", parent=styles["BodyText"], fontSize=7.8, leading=9.3, textColor=colors.HexColor("#475467"), spaceAfter=8))
    styles.add(ParagraphStyle(name="Missing", parent=styles["BodyText"], textColor=colors.HexColor("#b42318"), spaceAfter=6))
    styles.add(ParagraphStyle(name="ArtifactTitle", parent=styles["BodyText"], fontName="Helvetica-Bold", textColor=colors.HexColor("#101828"), spaceAfter=4))
    return styles


def _case_summary_table(test_cases, styles):
    rows = []
    for case in test_cases:
        status = case.get("status", "info")
        rows.append([Paragraph(f"{escape(case.get('name', 'Unnamed test'))} | <font color='{_status_color(status).hexval()}'>{escape(_stringify(status).upper())}</font>", styles["TableText"])])
    return _table(rows, [FULL_TABLE_WIDTH], has_header=False)


def _pairs_rows(value, styles, left_label="Field", right_label="Value", column_widths=(LABEL_COLUMN_WIDTH, CONTENT_COLUMN_WIDTH)):
    pairs = _pairs(value)
    if not pairs: return None
    rows = [[_paragraph(left_label, styles["TableText"]), _paragraph(right_label, styles["TableText"])]]
    rows.extend([[_paragraph(_label_text(label), styles["TableText"]), _paragraph(raw_value, styles["TableText"])] for label, raw_value in pairs])
    return _table(rows, list(column_widths))


def build_report(manifest, output_path):
    styles = _styles()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=42, bottomMargin=36, title=_stringify(manifest.get("title", "Test Report")))
    flow = []
    title = manifest.get("title", "Test Report")
    subtitle = manifest.get("subtitle", "")
    purpose = manifest.get("purpose", {})
    purpose_category = _purpose_category(purpose.get("category"))
    purpose_label = purpose.get("label") or PURPOSE_LABEL.get(purpose_category, PURPOSE_LABEL["mixed"])
    request_summary = manifest.get("request_summary", {})
    summary = manifest.get("summary", "")
    overview = manifest.get("overview", {})
    overview_status = overview.get("status", "info")
    overview_pairs = [(key.replace("_", " ").title(), value) for key, value in overview.items() if key != "status"]
    environment_pairs = _pairs(manifest.get("environment", {}))
    top_artifacts = manifest.get("artifacts", [])
    test_cases = manifest.get("test_cases", [])
    _validate_evidence_contract(test_cases)

    flow.append(_paragraph(title, _fit_header_style(styles["ReportTitle"], title, 22, 19, 17)))
    if subtitle: flow.append(_paragraph(subtitle, _fit_header_style(styles["ReportSubtitle"], subtitle, 14, 12, 10.8)))
    flow.append(Spacer(1, 0.12 * inch))
    overview_text = _compact_inline_pairs(overview_pairs)
    banner_parts = [f"<b>Purpose:</b> {escape(_stringify(purpose_label))}", f"<b>Status:</b> <font color='{_status_color(overview_status).hexval()}'>{escape(_stringify(overview_status).upper())}</font>"]
    if overview_text: banner_parts.append(escape(overview_text))
    flow.append(_meta_banner(" | ".join(banner_parts), styles))
    flow.append(Spacer(1, 0.08 * inch))

    summary_rows = []
    goal_parts = []
    if request_summary.get("requested_change"): goal_parts.append(f"Asked: {request_summary['requested_change']}")
    if request_summary.get("expected_outcome"): goal_parts.append(f"Expected: {request_summary['expected_outcome']}")
    if request_summary.get("scope"): goal_parts.append(f"Scope: {request_summary['scope']}")
    if goal_parts: summary_rows.append(("Goal", " | ".join(goal_parts)))
    if summary: summary_rows.append(("Result", summary))
    context_text = _compact_context(environment_pairs, manifest.get("generated_at"))
    if context_text: summary_rows.append(("Context", context_text))
    summary_table = _pairs_rows(summary_rows, styles, "Item", "Value")
    if summary_table:
        flow.append(_paragraph("Summary", styles["SectionTitle"]))
        flow.append(summary_table)
        flow.append(Spacer(1, 0.12 * inch))

    if top_artifacts:
        flow.extend(_artifact_blocks(top_artifacts, styles, section_title="Evidence"))

    if test_cases:
        flow.append(_paragraph("Verification Summary", styles["SectionTitle"]))
        if any(_comparison_enabled(manifest, case) for case in test_cases):
            flow.append(_paragraph("Case labels: the title row shows the function or case. Before and After are the compared states. Input is what was given. Used is the command, tool, or workflow that ran. Output is what came back. Why Pass is the acceptance reason.", styles["Caption"]))
        else:
            flow.append(_paragraph("Case labels: the title row shows the function or case. Input is what was given. Used is the command, tool, or workflow that ran. Output is what came back. Why Pass is the acceptance reason.", styles["Caption"]))
        flow.append(_case_summary_table(test_cases, styles))
        flow.append(Spacer(1, 0.12 * inch))

    for index, case in enumerate(test_cases, start=1):
        status = case.get("status", "info")
        case_name = _stringify(case.get("name", "Unnamed test"))
        function_name = _stringify(case.get("function_name", "")).strip()
        show_case_details = _show_case_details(manifest, case)
        case_title = f"Verification {index}: {function_name or case_name}"
        case_rows = [[Paragraph(f"{escape(case_title)} | <font color='{_status_color(status).hexval()}'>{escape(_stringify(status).upper())}</font>", styles["CaseHeader"]), ""]]
        case_details = dict(case.get("details") or {})
        case_is_comparison = _comparison_enabled(manifest, case)
        case_input_image = case.get("input_image_path") or case.get("input_image") or case_details.pop("input_image_path", "") or case_details.pop("input_image", "")
        case_used = _first_present_value(case, case_details, USED_FIELD_NAMES)
        case_pass_reason = _first_present_value(case, case_details, PASS_REASON_FIELD_NAMES)
        case_request = case.get("request") or case_details.pop("sample_request", "") or case_details.pop("request_example", "") or case_details.pop("request_payload", "")
        case_response = case.get("response") or case_details.pop("sample_response", "") or case_details.pop("response_example", "") or case_details.pop("response_payload", "") or case_details.pop("sample_output", "") or case_details.pop("sample_log_excerpt", "") or case_details.pop("log_excerpt", "")
        case_input = case_request or case.get("example_input") or case.get("input") or case.get("objective")
        if not case_input and case.get("steps"): case_input = " | ".join(_stringify(step) for step in case["steps"])
        has_concrete_input = bool(case_request or case.get("example_input") or case.get("input"))
        input_label = case.get("input_label") or ("Input" if has_concrete_input else "Check")
        case_output = case_response or case.get("example_output") or case.get("output") or case.get("result")
        has_concrete_output = bool(case_response or case.get("example_output") or case.get("output"))
        output_label = case.get("output_label") or ("Output" if has_concrete_output else "Result")
        case_summary = case.get("summary") or case.get("finding")
        if case_is_comparison:
            before_text = _comparison_value(case, case_details, "before")
            after_text = _comparison_value(case, case_details, "after")
            before_image_path = _comparison_value(case, case_details, "before_image_path")
            after_image_path = _comparison_value(case, case_details, "after_image_path")
            comparison_summary = _comparison_value(case, case_details, "summary") or case.get("finding")
            case_rows.append([Paragraph("<b>Before</b>", styles["TableText"]), _value_cell_value(before_text, before_image_path, styles, missing_label="before comparison evidence", width_limit=COMPARISON_INLINE_IMAGE_MAX_WIDTH, height_limit=COMPARISON_INLINE_IMAGE_MAX_HEIGHT)])
            case_rows.append([Paragraph("<b>After</b>", styles["TableText"]), _value_cell_value(after_text, after_image_path, styles, missing_label="after comparison evidence", width_limit=COMPARISON_INLINE_IMAGE_MAX_WIDTH, height_limit=COMPARISON_INLINE_IMAGE_MAX_HEIGHT)])
            if comparison_summary:
                case_rows.append([Paragraph("<b>Comparison</b>", styles["TableText"]), _paragraph(comparison_summary, styles["TableText"])])
                case_summary = ""
            if case_used:
                case_rows.append([Paragraph("<b>Used</b>", styles["TableText"]), _paragraph(case_used, styles["TableText"])])
            if case_output:
                case_rows.append([Paragraph(f"<b>{escape(_label_text(case.get('output_label') or 'Final Result'))}</b>", styles["TableText"]), _paragraph(case_output, styles["TableText"])])
            if case_pass_reason:
                case_rows.append([Paragraph("<b>Why Pass</b>", styles["TableText"]), _paragraph(case_pass_reason, styles["TableText"])])
        else:
            if case_input or case_input_image:
                case_rows.append([Paragraph(f"<b>{escape(_label_text(input_label))}</b>", styles["TableText"]), _input_cell_value(case_input, case_input_image, styles)])
            if case_used:
                case_rows.append([Paragraph("<b>Used</b>", styles["TableText"]), _paragraph(case_used, styles["TableText"])])
            if case_output:
                case_rows.append([Paragraph(f"<b>{escape(_label_text(output_label))}</b>", styles["TableText"]), _paragraph(case_output, styles["TableText"])])
            elif case_summary:
                case_rows.append([Paragraph("<b>Result</b>", styles["TableText"]), _paragraph(case_summary, styles["TableText"])])
                case_summary = ""
            if case_pass_reason:
                case_rows.append([Paragraph("<b>Why Pass</b>", styles["TableText"]), _paragraph(case_pass_reason, styles["TableText"])])
        if show_case_details:
            if case_summary:
                case_rows.append([Paragraph("<b>Summary</b>", styles["TableText"]), _paragraph(case_summary, styles["TableText"])])
            if function_name and case_name and case_name != function_name:
                case_rows.append([Paragraph("<b>Scenario</b>", styles["TableText"]), _paragraph(case_name, styles["TableText"])])
            for label, raw_value in _pairs(case_details):
                case_rows.append([Paragraph(f"<b>{escape(_label_text(label))}</b>", styles["TableText"]), _paragraph(raw_value, styles["TableText"])])
            notes = case.get("notes", [])
            if notes:
                case_rows.append([Paragraph("<b>Notes</b>", styles["TableText"]), Paragraph(_bullet_lines(notes), styles["TableText"])])
        elif len(case_rows) == 1:
            fallback_pairs = _pairs(case_details)
            if fallback_pairs:
                label, raw_value = fallback_pairs[0]
                case_rows.append([Paragraph(f"<b>{escape(_label_text(label))}</b>", styles["TableText"]), _paragraph(raw_value, styles["TableText"])])
            else:
                notes = case.get("notes", [])
                if notes:
                    case_rows.append([Paragraph("<b>Result</b>", styles["TableText"]), Paragraph(_bullet_lines(notes), styles["TableText"])])
        case_table = Table(case_rows, colWidths=[LABEL_COLUMN_WIDTH, CONTENT_COLUMN_WIDTH], hAlign="LEFT", splitByRow=1)
        case_table.setStyle(TableStyle([
            ("SPAN", (0, 0), (1, 0)),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d5dd")),
            ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#f2f4f7")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fcfcfd")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        flow.append(case_table)
        case_artifacts = case.get("artifacts") or case.get("images") or []
        if case_artifacts:
            flow.append(Spacer(1, 0.08 * inch))
            flow.extend(_artifact_blocks(case_artifacts, styles, width_limit=FULL_TABLE_WIDTH, height_limit=3.7 * inch, spacer_height=0.08 * inch))
        flow.append(Spacer(1, 0.12 * inch))

    doc.build(flow, onFirstPage=_page_number, onLaterPages=_page_number)


def _page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#475467"))
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 0.4 * inch, f"Page {doc.page}")
    canvas.restoreState()


def main():
    parser = argparse.ArgumentParser(description="Generate a visual PDF test report from a JSON manifest.")
    parser.add_argument("--input", required=True, help="Path to the manifest JSON file.")
    parser.add_argument("--output", required=True, help="Path to the output PDF file.")
    parser.add_argument("--cleanup-root", help="Optional report-cache root where stale PDFs should be removed.")
    parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS, help="Delete cached report PDFs not used for this many days. Default: 7.")
    parser.add_argument("--skip-cleanup", action="store_true", help="Disable stale cached report cleanup.")
    args = parser.parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    with input_path.open("r", encoding="utf-8") as input_file: manifest = json.load(input_file)
    build_report(manifest, output_path)
    if not args.skip_cleanup:
        cleanup_root = _resolve_cleanup_root(output_path, args.cleanup_root)
        deleted_paths = cleanup_old_reports(cleanup_root, retention_days=args.retention_days, keep_paths=[output_path])
        if deleted_paths: print(f"Cleaned {len(deleted_paths)} stale report PDF(s) from {cleanup_root}", file=sys.stderr)
    print(output_path)


if __name__ == "__main__": main()
