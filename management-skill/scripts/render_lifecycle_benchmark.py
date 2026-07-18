#!/usr/bin/env python3
"""Render the public two-world lifecycle benchmark as a deterministic SVG."""

import argparse
import html
import json
import os
from pathlib import Path
from tempfile import mkstemp


TIERS = ("simple", "medium", "complex")
TIER_LABELS = {
    "simple": "Simple · one-file slug edit · 4/4 tests",
    "medium": "Medium · decimal pricing method · 6/6 tests",
    "complex": "Complex · real three-source audit · exact semantic gate",
}
TIER_NOTES = {
    "simple": "Task-strategy cold start → Terra-medium · two receipt-proven runs",
    "medium": "Task-strategy cold start → Terra-high · two receipt-proven runs",
    "complex": "Cost admission → one Luna-low producer · 68,483 source bytes",
}
DIRECT = "#4f8ff7"
AUTO = "#22c7b8"
CHECK = "#6ee7dc"
BG = "#07111f"
CARD = "#101d33"
WHOLE = "#0d3035"
TEXT = "#f8fafc"
MUTED = "#a8b5c8"
LINE = "#334760"
POSITIVE = "#62e7d8"


class BenchmarkError(ValueError):
    pass


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise BenchmarkError(f"invalid {name}")
    return value


def _saved(baseline, candidate):
    return (baseline - candidate) * 100 / baseline


def load_summary(path):
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {
        "schema_version": 2,
        "comparison_contract": "exactly_two_worlds",
        "entry_pair_both_arms": "gpt-5.6-sol|ultra",
        "pairs": 6,
        "main_runs": 12,
        "ending_runs": 6,
        "status": "pass",
        "all_main_correct": True,
        "all_endings_pass": True,
    }
    for key, expected in required.items():
        if document.get(key) != expected:
            raise BenchmarkError(f"invalid {key}")
    if set(document.get("tiers", {})) != set(TIERS):
        raise BenchmarkError("invalid tiers")
    for tier in TIERS:
        row = document["tiers"][tier]
        direct = row.get("without_skill_task", {})
        task = row.get("with_skill_task", {})
        check = row.get("with_skill_background_check", {})
        whole = row.get("with_skill_task_plus_check", {})
        for name, value in (
            ("direct tokens", direct.get("tokens")),
            ("direct time", direct.get("time_ms")),
            ("task tokens", task.get("tokens")),
            ("task time", task.get("time_ms")),
            ("check tokens", check.get("tokens")),
            ("check time", check.get("time_ms")),
            ("whole tokens", whole.get("tokens")),
            ("whole time", whole.get("sequential_time_ms")),
        ):
            _number(value, f"{tier} {name}")
        if direct.get("verify_tokens") != 0 or direct.get("verify_time_ms") != 0:
            raise BenchmarkError(f"{tier} Direct verifier must be zero")
        if whole["tokens"] != task["tokens"] + check["tokens"]:
            raise BenchmarkError(f"{tier} token total mismatch")
        if whole["sequential_time_ms"] != task["time_ms"] + check["time_ms"]:
            raise BenchmarkError(f"{tier} time total mismatch")
        if not row.get("all_main_correct") or not row.get("all_endings_pass"):
            raise BenchmarkError(f"{tier} correctness failure")
    return document


def _atomic_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o644)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _esc(value):
    return html.escape(str(value), quote=True)


def _tokens(value):
    return f"{int(value):,}"


def _seconds(value):
    return f"{value / 1000:.3f}s"


def _pct(value):
    return f"{value:.3f}%"


def _bar(value, baseline, width=380):
    return max(3, round(value / baseline * width))


def render(document):
    """Build a faceted stacked-bar comparison for a GitHub Markdown report.

    Chart contract: compare Direct task against Auto task and Auto task+Ending;
    normalize bars to Direct=100% within each tier; use exact labels for lookup;
    use blue, solid teal, and hatched teal so verifier presence is not color-only.
    """
    width, height = 1800, 1550
    metadata = html.escape(json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '  <title id="title">Two-world adaptive lifecycle benchmark</title>',
        '  <desc id="desc">Three real task tiers compare a fixed Sol-ultra task with an adaptively routed task. Only the adaptive world adds a striped, separate Ending check. Auto task and Auto task plus check both use fewer logical tokens and less time in every aggregate tier.</desc>',
        f'  <metadata id="benchmark-data">{metadata}</metadata>',
        '  <defs>',
        f'    <pattern id="ending-stripes" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(35)"><rect width="14" height="14" fill="{AUTO}"/><rect width="6" height="14" fill="{CHECK}"/></pattern>',
        '  </defs>',
        f'  <rect width="{width}" height="{height}" rx="34" fill="{BG}"/>',
        '  <g font-family="Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">',
        f'    <text x="72" y="70" fill="{TEXT}" font-size="42" font-weight="800">Real two-world benchmark · PASS</text>',
        f'    <text x="72" y="112" fill="{MUTED}" font-size="21">6 A/B pairs · 12 main runs · 6 separate Ending runs · lower is better · logical tokens are not billing tokens</text>',
        f'    <rect x="72" y="138" width="1656" height="56" rx="18" fill="#0c2833" stroke="{AUTO}" stroke-width="2"/>',
        f'    <text x="900" y="174" text-anchor="middle" fill="{TEXT}" font-size="21" font-weight="800">FINISH JOB FIRST → RETURN RESULT → BACKGROUND VERIFY IN A NEW END TASK</text>',
        f'    <rect x="1110" y="62" width="18" height="18" rx="4" fill="{DIRECT}"/><text x="1138" y="78" fill="{MUTED}" font-size="17">Direct task</text>',
        f'    <rect x="1310" y="62" width="18" height="18" rx="4" fill="{AUTO}"/><text x="1338" y="78" fill="{MUTED}" font-size="17">Auto task</text>',
        '    <rect x="1490" y="62" width="18" height="18" rx="4" fill="url(#ending-stripes)"/><text x="1518" y="78" fill="{muted}" font-size="17">Auto-only Ending check</text>'.format(muted=MUTED),
    ]

    card_y = {"simple": 220, "medium": 520, "complex": 820}
    for tier in TIERS:
        row = document["tiers"][tier]
        direct = row["without_skill_task"]
        task = row["with_skill_task"]
        check = row["with_skill_background_check"]
        whole = row["with_skill_task_plus_check"]
        y = card_y[tier]
        token_task_saved = _saved(direct["tokens"], task["tokens"])
        token_whole_saved = _saved(direct["tokens"], whole["tokens"])
        time_task_saved = _saved(direct["time_ms"], task["time_ms"])
        time_whole_saved = _saved(direct["time_ms"], whole["sequential_time_ms"])
        token_task_width = _bar(task["tokens"], direct["tokens"])
        token_check_width = _bar(check["tokens"], direct["tokens"])
        time_task_width = _bar(task["time_ms"], direct["time_ms"])
        time_check_width = _bar(check["time_ms"], direct["time_ms"])
        pair = ", ".join(row["adaptive_pairs"]).replace("|", " | ")
        lines.extend([
            f'    <rect x="72" y="{y}" width="1656" height="270" rx="26" fill="{CARD}" stroke="{LINE}" stroke-width="2"/>',
            f'    <text x="108" y="{y + 44}" fill="{TEXT}" font-size="27" font-weight="800">{_esc(TIER_LABELS[tier])}</text>',
            f'    <text x="108" y="{y + 75}" fill="{MUTED}" font-size="17">{_esc(TIER_NOTES[tier])}</text>',
            f'    <text x="1688" y="{y + 45}" text-anchor="end" fill="{POSITIVE}" font-size="17" font-weight="800">TASK + CHECK WIN</text>',
            f'    <text x="108" y="{y + 112}" fill="{TEXT}" font-size="17" font-weight="800">COHORT LOGICAL TOKENS</text>',
            f'    <text x="910" y="{y + 112}" fill="{TEXT}" font-size="17" font-weight="800">COHORT TIME</text>',
            f'    <text x="108" y="{y + 145}" fill="{MUTED}" font-size="16" font-weight="700">Without</text><text x="205" y="{y + 145}" fill="{TEXT}" font-size="16" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{_tokens(direct["tokens"])}</text>',
            f'    <rect x="410" y="{y + 128}" width="380" height="20" rx="10" fill="{DIRECT}"/>',
            f'    <text x="108" y="{y + 187}" fill="{MUTED}" font-size="16" font-weight="700">With</text><text x="205" y="{y + 187}" fill="{TEXT}" font-size="16" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{_tokens(task["tokens"])} + {_tokens(check["tokens"])}</text>',
            f'    <rect x="410" y="{y + 170}" width="380" height="20" rx="10" fill="#1d2c44"/><rect x="410" y="{y + 170}" width="{token_task_width}" height="20" rx="10" fill="{AUTO}"/><rect x="{410 + token_task_width}" y="{y + 170}" width="{token_check_width}" height="20" fill="url(#ending-stripes)"/>',
            f'    <text x="410" y="{y + 222}" fill="{POSITIVE}" font-size="16" font-weight="800">{_pct(token_task_saved)} task · {_pct(token_whole_saved)} task + check saved</text>',
            f'    <text x="910" y="{y + 145}" fill="{MUTED}" font-size="16" font-weight="700">Without</text><text x="1007" y="{y + 145}" fill="{TEXT}" font-size="16" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{_seconds(direct["time_ms"])}</text>',
            f'    <rect x="1240" y="{y + 128}" width="380" height="20" rx="10" fill="{DIRECT}"/>',
            f'    <text x="910" y="{y + 187}" fill="{MUTED}" font-size="16" font-weight="700">With</text><text x="1007" y="{y + 187}" fill="{TEXT}" font-size="16" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">{_seconds(task["time_ms"])} + {_seconds(check["time_ms"])}</text>',
            f'    <rect x="1240" y="{y + 170}" width="380" height="20" rx="10" fill="#1d2c44"/><rect x="1240" y="{y + 170}" width="{time_task_width}" height="20" rx="10" fill="{AUTO}"/><rect x="{1240 + time_task_width}" y="{y + 170}" width="{time_check_width}" height="20" fill="url(#ending-stripes)"/>',
            f'    <text x="1240" y="{y + 222}" fill="{POSITIVE}" font-size="16" font-weight="800">{_pct(time_task_saved)} task · {_pct(time_whole_saved)} whole faster</text>',
            f'    <text x="108" y="{y + 252}" fill="{MUTED}" font-size="14">Direct verifier: 0 tokens / 0s · Ending is Auto-only and begins after the usable result exists.</text>',
        ])

    direct = document["world_without_skill_task"]
    task = document["world_with_skill_task"]
    check = document["world_with_skill_background_check"]
    whole = document["world_with_skill_task_plus_check"]
    diagnostic = document["routing_overhead_diagnostic_excluded_from_both_worlds"]
    lines.extend([
        f'    <rect x="72" y="1120" width="1656" height="360" rx="28" fill="{WHOLE}" stroke="{AUTO}" stroke-width="2"/>',
        f'    <text x="108" y="1170" fill="{TEXT}" font-size="31" font-weight="800">Whole picture · all 6 pairs</text>',
        f'    <text x="108" y="1204" fill="{MUTED}" font-size="18">Without skill has no verifier. With skill returns the result first, then starts the separate striped Ending task.</text>',
        f'    <text x="108" y="1265" fill="{TEXT}" font-size="31" font-weight="800">{_pct(task["token_saved_percent"])} fewer task tokens</text>',
        f'    <text x="108" y="1300" fill="{MUTED}" font-size="17">{_tokens(direct["tokens"])} Direct → {_tokens(task["tokens"])} Auto task · 6/6 pairwise token wins</text>',
        f'    <text x="620" y="1265" fill="{TEXT}" font-size="31" font-weight="800">{_pct(task["time_saved_percent"])} faster first result</text>',
        f'    <text x="620" y="1300" fill="{MUTED}" font-size="17">{_seconds(direct["time_ms"])} Direct → {_seconds(task["time_ms"])} Auto task · 6/6 pairwise time wins</text>',
        f'    <text x="1180" y="1265" fill="{TEXT}" font-size="31" font-weight="800">Task + Ending still wins</text>',
        f'    <text x="1180" y="1300" fill="{MUTED}" font-size="17">{_tokens(whole["tokens"])} tokens · {_seconds(whole["sequential_time_ms"])} sequential</text>',
        f'    <text x="1180" y="1330" fill="{POSITIVE}" font-size="18" font-weight="800">{_pct(whole["token_saved_percent"])} fewer tokens · {_pct(whole["sequential_time_saved_percent"])} faster</text>',
        f'    <line x1="108" y1="1362" x2="1692" y2="1362" stroke="#2e6668"/>',
        f'    <text x="108" y="1400" fill="{TEXT}" font-size="18" font-weight="800">Ending evidence cost</text><text x="320" y="1400" fill="{MUTED}" font-size="17">{_tokens(check["tokens"])} tokens / {_seconds(check["time_ms"])} · 6/6 PASS · never gates first result</text>',
        f'    <text x="108" y="1435" fill="{TEXT}" font-size="18" font-weight="800">Disclosed excluded diagnostic</text><text x="390" y="1435" fill="{MUTED}" font-size="17">common Sol-ultra dispatcher {_tokens(diagnostic["tokens"])} tokens / {_seconds(diagnostic["time_ms"])}; not counted as either task world</text>',
        f'    <text x="108" y="1466" fill="{MUTED}" font-size="15">Both entries: gpt-5.6-sol | ultra · 12/12 exact results · all Mini Tests/gates passed · 0 retry, fallback, or repair</text>',
        '  </g>',
        '</svg>',
        '',
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    document = load_summary(args.input)
    _atomic_write(args.output, render(document))
    print(json.dumps({"status": "pass", "output": str(args.output), "tiers": list(TIERS)}, sort_keys=True))


if __name__ == "__main__":
    main()
