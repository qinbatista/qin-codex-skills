#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


MODEL_SLUGS = ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.3-codex-spark"]


def cache_models(models_cache_path):
    cache = json.loads(models_cache_path.read_text(encoding="utf-8"))
    return cache, {model["slug"]: model for model in cache["models"]}


def missing_required_models(models_cache_path):
    _, models_by_slug = cache_models(models_cache_path)
    return [slug for slug in MODEL_SLUGS if slug not in models_by_slug]


def snapshot_has_required_models(snapshot):
    return all(f"`{slug}`" in snapshot for slug in MODEL_SLUGS) and all(text in snapshot for text in ["low, medium, high, xhigh, max, ultra", "low, medium, high, xhigh, max", "low, medium, high, xhigh"])


def check_snapshot(models_cache_path, snapshot):
    missing_slugs = missing_required_models(models_cache_path)
    if missing_slugs:
        valid = snapshot_has_required_models(snapshot)
        return {"valid": valid, "status": "cache-incomplete-preserved" if valid else "cache-incomplete-and-snapshot-invalid", "missing_cache_models": missing_slugs}
    desired = build_snapshot(models_cache_path)
    return {"valid": snapshot == desired, "status": "current" if snapshot == desired else "stale", "missing_cache_models": []}


def build_snapshot(models_cache_path):
    cache, models_by_slug = cache_models(models_cache_path)
    missing_slugs = [slug for slug in MODEL_SLUGS if slug not in models_by_slug]
    if missing_slugs:
        raise ValueError(f"models cache is missing required models: {', '.join(missing_slugs)}")
    lines = ["# Cached Model Capabilities", "", "Use this local snapshot during `task-analyze-skill`. Do not query the runtime model catalog on every task. Refresh only when the user asks for current capabilities, this file is missing, the runtime rejects a model/effort, or the model list changes.", "", "If a refreshed cache omits one of these models while the current Codex UI/runtime still executes it, preserve this last validated snapshot, report the cache as incomplete, and require a runtime receipt before using or changing that route.", "", "- Source: `~/.codex/models_cache.json`", f"- Codex client version: `{cache['client_version']}`", "", "| Display name | Model ID | Inputs | Context | API | Default effort | Supported efforts | Speed tiers |", "|---|---|---|---:|---|---|---|---|"]
    for slug in MODEL_SLUGS:
        model = models_by_slug[slug]
        efforts = ", ".join(level["effort"] for level in model["supported_reasoning_levels"])
        inputs = ", ".join(model["input_modalities"])
        api_support = "yes" if model["supported_in_api"] else "no"
        speed_tiers = ", ".join(model.get("additional_speed_tiers", [])) or "default"
        lines.append(f"| {model['display_name']} | `{slug}` | {inputs} | {model['context_window']:,} | {api_support} | `{model['default_reasoning_level']}` | {efforts} | {speed_tiers} |")
    lines.extend(["", "## Effort Compatibility", "", "- `GPT-5.6-Sol`: low, medium, high, xhigh, max, ultra.", "- `GPT-5.6-Terra`: low, medium, high, xhigh, max, ultra.", "- `GPT-5.6-Luna`: low, medium, high, xhigh, max.", "- `GPT-5.3-Codex-Spark`: low, medium, high, xhigh.", "- Sol, Terra, and Luna accept image input. Spark is text-only.", "- Spark is unavailable through API-only execution surfaces.", "- If an effort is unsupported, use the highest supported effort below it and show the normalization.", "", "## Refresh", "", "```bash", "python3 scripts/sync_model_capabilities.py", "python3 scripts/sync_model_capabilities.py --check", "```", ""])
    return "\n".join(lines)


def main():
    skill_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Sync task-analyze-skill model capabilities from the local Codex model cache.")
    parser.add_argument("--models-cache", type=Path, default=Path.home() / ".codex" / "models_cache.json")
    parser.add_argument("--output", type=Path, default=skill_dir / "references" / "model-capabilities.md")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    models_cache_path = args.models_cache.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    if args.check:
        if not output_path.exists():
            print(f"model capability snapshot is stale: {output_path}")
            return 1
        status = check_snapshot(models_cache_path, output_path.read_text(encoding="utf-8"))
        if status["status"] == "cache-incomplete-preserved":
            print(f"model cache is incomplete; preserved last structurally valid snapshot: {', '.join(status['missing_cache_models'])}")
        else:
            print(f"model capability snapshot is {status['status']}: {output_path}")
        return 0 if status["valid"] else 1
    missing_slugs = missing_required_models(models_cache_path)
    if missing_slugs:
        print(f"refusing to overwrite the validated snapshot from an incomplete model cache: {', '.join(missing_slugs)}")
        return 1
    snapshot = build_snapshot(models_cache_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(snapshot, encoding="utf-8")
    print(f"model capability snapshot updated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
