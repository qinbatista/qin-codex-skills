#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


FORBIDDEN_SKILL_NAME_PATTERNS = (
    "qin-easy-code-spark",
    "qin-karpathy-guidelines",
    "qin-prompt-creating",
    "qin-python-code-checker",
    "qin-unity-csharp-minimal-style",
    "qin-done-means-tested",
    "qin-test-pdf-report",
    "qin-image-editing-workflow",
    "qin-skill-optimization",
    "qin-ui-review",
    "qin-codex-auth-swithc",
    "qin-codex-skills-github-sync",
    "qin-git-push-safety",
)
REQUIRED_COMMON_SECTIONS = ("Generated File Placement", "Internal Route Selection")
LONG_REFERENCE_LINE_LIMIT = 100
SKILL_BODY_LINE_WARNING = 220
SKILL_BODY_LINE_LIMIT = 500


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text, ["missing opening frontmatter marker"]
    end_index = text.find("\n---\n", 4)
    if end_index == -1:
        return {}, text, ["missing closing frontmatter marker"]
    frontmatter_text = text[4:end_index]
    metadata = {}
    errors = []
    for line in frontmatter_text.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, text[end_index + 5 :], errors


def headings(text):
    return [line.lstrip("#").strip() for line in text.splitlines() if line.startswith("#")]


def local_links(text):
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)


def command_paths(text):
    return re.findall(r"(?<!\w)(?:\./|\.\./|scripts/|references/)[^\s\"'`]+", text)


def resolve_reference(raw_path, skill_dir):
    clean_path = raw_path.split("#", 1)[0].strip()
    if not clean_path or re.match(r"^[a-z]+://", clean_path):
        return None
    path = Path(clean_path).expanduser()
    if path.is_absolute():
        return path
    return (skill_dir / path).resolve()


def has_toc(text):
    lower_text = text.lower()
    return "table of contents" in lower_text or "## contents" in lower_text or "## 目录" in lower_text


def audit_skill(skill_dir):
    skill_file = skill_dir / "SKILL.md"
    result = {
        "skill": skill_dir.name,
        "path": str(skill_dir),
        "errors": [],
        "warnings": [],
        "info": [],
    }
    if not skill_file.exists():
        result["errors"].append("missing SKILL.md")
        return result

    text = skill_file.read_text(encoding="utf-8")
    metadata, body, frontmatter_errors = split_frontmatter(text)
    result["errors"].extend(frontmatter_errors)
    if set(metadata) != {"name", "description"}:
        result["errors"].append(f"frontmatter keys must be exactly name and description, got {sorted(metadata)}")
    if metadata.get("name") != skill_dir.name:
        result["errors"].append(f"frontmatter name {metadata.get('name')!r} does not match folder {skill_dir.name!r}")
    description = metadata.get("description", "")
    if not description:
        result["errors"].append("description is empty")
    elif not re.search(r"\bUse (when|at|for)\b", description):
        result["warnings"].append("description may not clearly state trigger conditions with Use when/at/for")
    if len(description) > 850:
        result["warnings"].append("description is long; trigger metadata may waste context")
    if any(pattern in text for pattern in FORBIDDEN_SKILL_NAME_PATTERNS):
        result["errors"].append("old qin-* skill name reference found")

    skill_headings = headings(body)
    for section in REQUIRED_COMMON_SECTIONS:
        if section not in skill_headings:
            result["warnings"].append(f"missing common section: {section}")
    if len(text.splitlines()) > SKILL_BODY_LINE_LIMIT:
        result["errors"].append(f"SKILL.md has more than {SKILL_BODY_LINE_LIMIT} lines")
    elif len(text.splitlines()) > SKILL_BODY_LINE_WARNING:
        result["warnings"].append(f"SKILL.md has {len(text.splitlines())} lines; consider moving details into references/")

    for raw_link in local_links(text):
        resolved_path = resolve_reference(raw_link, skill_dir)
        if resolved_path and not resolved_path.exists():
            result["errors"].append(f"missing linked file: {raw_link}")
    for raw_path in command_paths(text):
        resolved_path = resolve_reference(raw_path.rstrip(".,)"), skill_dir)
        if resolved_path and not resolved_path.exists():
            result["errors"].append(f"missing command/reference path: {raw_path}")

    for reference_path in sorted((skill_dir / "references").glob("*.md")) if (skill_dir / "references").exists() else []:
        reference_text = reference_path.read_text(encoding="utf-8")
        line_count = len(reference_text.splitlines())
        if line_count > LONG_REFERENCE_LINE_LIMIT and not has_toc(reference_text):
            result["warnings"].append(f"{reference_path.relative_to(skill_dir)} has {line_count} lines and no table of contents")

    for noisy_path in skill_dir.rglob("*"):
        if noisy_path.name in {".DS_Store", "__pycache__"}:
            result["warnings"].append(f"local noise path exists: {noisy_path.relative_to(skill_dir)}")

    return result


def collect_skill_dirs(skills_root):
    return sorted(
        [
            path for path in skills_root.iterdir()
            if path.is_dir() and not path.name.startswith(".") and (path / "SKILL.md").exists()
        ],
        key=lambda path: path.name,
    )


def main():
    parser = argparse.ArgumentParser(description="Audit user global Codex skills against the official skill-creator structure rules.")
    parser.add_argument("skills_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    results = [audit_skill(skill_dir) for skill_dir in collect_skill_dirs(args.skills_root.expanduser().resolve())]
    summary = {
        "skills_root": str(args.skills_root.expanduser().resolve()),
        "skill_count": len(results),
        "error_count": sum(len(result["errors"]) for result in results),
        "warning_count": sum(len(result["warnings"]) for result in results),
        "results": results,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"skills={summary['skill_count']} errors={summary['error_count']} warnings={summary['warning_count']}")
    for result in results:
        status = "fail" if result["errors"] else "warn" if result["warnings"] else "pass"
        print(f"- {result['skill']}: {status}; errors={len(result['errors'])}; warnings={len(result['warnings'])}")
        for error in result["errors"]:
            print(f"  error: {error}")
        for warning in result["warnings"]:
            print(f"  warning: {warning}")
    return 1 if summary["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
