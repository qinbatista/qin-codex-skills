#!/usr/bin/env python3

import argparse
import base64
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

try:
    from wcwidth import wcswidth
except Exception:
    wcswidth = None

HANDSHAKE_PREFIX = 'Request: "GET /backend-api/codex/responses'
TOKEN_COUNT_TYPE = "token_count"
DEFAULT_LIVE_PROMPT = "Reply with exactly OK."
RETRY_AFTER_PATTERN = re.compile(r"try again at ([^.]+)", re.IGNORECASE)
LIVE_CACHE_FILENAME = "auth_status_cache.json"
LIVE_PROBE_MAX_WORKERS = 4
PROFILE_DISCOVERY_MAX_WORKERS = 8
BASE_TABLE_COLUMN_COUNT = 7
BASE_TABLE_MIN_WIDTHS = [22, 22, 18, 10, 27, 27, 34]
TABLE_SEPARATOR = "  |  "


def load_json(path):
    with path.open() as handle:
        return json.load(handle)


def decode_jwt_payload(token):
    if not isinstance(token, str) or token.count(".") < 2:
        return {}
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return {}


def iso_to_local_text(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def iso_to_pretty_local_text(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return parsed.astimezone().strftime("%B %-d, %Y %-I:%M %p %Z")


def parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def unix_to_local_text(value):
    if value is None:
        return None
    try:
        parsed = datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone()
    except Exception:
        return None
    return parsed.strftime("%Y-%m-%d %H:%M:%S %Z")


def unix_to_pretty_local_text(value):
    if value is None:
        return None
    try:
        parsed = datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone()
    except Exception:
        return None
    return parsed.strftime("%B %-d, %Y %-I:%M %p %Z")


def human_time_to_pretty_local_text(value):
    if not value:
        return None
    cleaned = re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", value.strip(), flags=re.IGNORECASE)
    local_tz = datetime.now().astimezone().tzinfo
    for fmt in ("%b %d, %Y %I:%M %p", "%B %d, %Y %I:%M %p"):
        try:
            parsed = datetime.strptime(cleaned, fmt).replace(tzinfo=local_tz)
        except ValueError:
            continue
        return parsed.strftime("%B %-d, %Y %-I:%M %p %Z")
    return cleaned


def normalize_percent(value):
    if value is None:
        return None
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return None


def remaining_percent(used_percent):
    used_value = normalize_percent(used_percent)
    if used_value is None:
        return None
    return max(0.0, min(100.0, 100.0 - used_value))


def extract_retry_after_text(error_message):
    if not error_message:
        return None
    match = RETRY_AFTER_PATTERN.search(error_message)
    if not match:
        return None
    return match.group(1).strip()


def is_limit_hit_error(error_message):
    normalized = (error_message or "").lower()
    if not normalized:
        return False
    return (
        "usage limit" in normalized
        or "try again at" in normalized
        or "purchase more credits" in normalized
        or "request to your admin" in normalized
    )


def explain_error_reason(error_message):
    normalized = (error_message or "").lower()
    if not normalized:
        return None
    if "refresh token was already used" in normalized:
        return "refresh token already used"
    if "could not be refreshed" in normalized or "sign in again" in normalized:
        return "login expired"
    if "invalid refresh token" in normalized or "invalid_grant" in normalized:
        return "login invalid"
    if "unauthorized" in normalized or "401" in normalized:
        return "login invalid"
    if "request to your admin" in normalized:
        return "team usage limit reached"
    if "purchase more credits" in normalized:
        return "credits exhausted"
    if "upgrade to pro" in normalized:
        return "personal plan limit reached"
    if "usage limit" in normalized or "try again at" in normalized:
        return "usage limit reached"
    if "forbidden" in normalized or "403" in normalized:
        return "request blocked"
    return "request failed"


def guess_plan_type(rate_limits, error_message):
    rate_limits = rate_limits or {}
    if rate_limits.get("plan_type"):
        return rate_limits["plan_type"]
    normalized = (error_message or "").lower()
    if "request to your admin" in normalized:
        return "team"
    return None


def build_usage_snapshot(rate_limits, observed_at, source_rollout_path, error_message=None):
    rate_limits = rate_limits or {}
    primary = rate_limits.get("primary") or {}
    secondary = rate_limits.get("secondary") or {}
    primary_used = normalize_percent(primary.get("used_percent"))
    secondary_used = normalize_percent(secondary.get("used_percent"))
    return {
        "observed_at": observed_at,
        "observed_at_text": iso_to_local_text(observed_at),
        "plan_type": guess_plan_type(rate_limits, error_message),
        "limit_id": rate_limits.get("limit_id"),
        "limit_name": rate_limits.get("limit_name"),
        "primary_used_percent": primary_used,
        "primary_remaining_percent": remaining_percent(primary_used),
        "primary_window_minutes": primary.get("window_minutes"),
        "primary_resets_at": primary.get("resets_at"),
        "primary_resets_at_text": unix_to_local_text(primary.get("resets_at")),
        "primary_resets_at_pretty_text": unix_to_pretty_local_text(primary.get("resets_at")),
        "secondary_used_percent": secondary_used,
        "secondary_remaining_percent": remaining_percent(secondary_used),
        "secondary_window_minutes": secondary.get("window_minutes"),
        "secondary_resets_at": secondary.get("resets_at"),
        "secondary_resets_at_text": unix_to_local_text(secondary.get("resets_at")),
        "secondary_resets_at_pretty_text": unix_to_pretty_local_text(secondary.get("resets_at")),
        "credits": rate_limits.get("credits"),
        "source_rollout_path": source_rollout_path,
        "error_message": error_message,
        "retry_after_text": extract_retry_after_text(error_message),
        "limit_hit": is_limit_hit_error(error_message),
        "error_reason_text": explain_error_reason(error_message),
    }


def profile_alias(path):
    stem = path.stem
    if stem == "auth":
        return "active"
    alias = re.sub(r"^auth[\s_-]*", "", stem, flags=re.IGNORECASE).strip().lower()
    return alias or "active"


def build_selector_variants(*values):
    variants = []
    for value in values:
        raw = (value or "").strip().lower()
        if not raw:
            continue
        variants.append(raw)
        normalized = re.sub(r"[\s_-]+", " ", raw).strip()
        if not normalized:
            continue
        variants.append(normalized)
        tokens = normalized.split()
        variants.append("_".join(tokens))
        variants.append("-".join(tokens))
        variants.append("".join(tokens))
    return unique_preserve_order(variants)


def unique_preserve_order(items):
    seen = set()
    result = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def normalize_backup_filename(name):
    raw = name.strip()
    if not raw:
        raise ValueError("Backup name cannot be empty.")
    if raw.lower().startswith("auth") and raw.lower().endswith(".json"):
        filename = Path(raw).name
    else:
        slug = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
        if not slug:
            raise ValueError("Backup name must contain at least one letter or digit.")
        filename = f"auth_{slug}.json"
    if filename == "auth.json":
        raise ValueError("Backup target cannot be auth.json. Use a backup name like 'ben' or 'work'.")
    return filename


def build_live_cache_path(codex_home):
    return codex_home / LIVE_CACHE_FILENAME


def load_live_cache(codex_home):
    cache_path = build_live_cache_path(codex_home)
    if not cache_path.exists():
        return {}
    try:
        payload = load_json(cache_path)
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict):
        return {}
    return profiles


def write_live_cache(codex_home, profiles):
    cache_path = build_live_cache_path(codex_home)
    payload = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "profiles": {},
    }
    for profile in profiles:
        usage = profile.get("usage")
        if not usage:
            continue
        payload["profiles"][profile["file"]] = {
            "file": profile["file"],
            "account_id": profile.get("account_id"),
            "subject": profile.get("subject"),
            "email": profile.get("email"),
            "usage": usage,
        }
    try:
        cache_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    except OSError:
        pass


def same_profile_identity(profile, cached_entry):
    return (
        (profile.get("account_id") or "") == (cached_entry.get("account_id") or "")
        and (profile.get("subject") or "") == (cached_entry.get("subject") or "")
        and (profile.get("email") or "") == (cached_entry.get("email") or "")
    )


def newer_usage(primary_usage, secondary_usage):
    if not primary_usage:
        return secondary_usage
    if not secondary_usage:
        return primary_usage
    primary_at = parse_iso_datetime(primary_usage.get("observed_at"))
    secondary_at = parse_iso_datetime(secondary_usage.get("observed_at"))
    if primary_at and secondary_at:
        return primary_usage if primary_at >= secondary_at else secondary_usage
    if secondary_at:
        return secondary_usage
    return primary_usage


def choose_cached_or_fallback_usage(profile, fallback_usage, cached_profiles):
    cached_entry = cached_profiles.get(profile["file"])
    if not cached_entry or not same_profile_identity(profile, cached_entry):
        return fallback_usage
    cached_usage = cached_entry.get("usage")
    if not isinstance(cached_usage, dict):
        return fallback_usage
    cached_usage = dict(cached_usage)
    cached_usage["source"] = "last-live-cache"
    return newer_usage(cached_usage, fallback_usage)


def load_recent_rollout_paths(codex_home, limit):
    state_db = codex_home / "state_5.sqlite"
    rollout_paths = []
    seen = set()
    if state_db.exists():
        try:
            con = sqlite3.connect(state_db)
            cur = con.cursor()
            rows = cur.execute(
                "select rollout_path from threads order by updated_at desc limit ?",
                (limit,),
            ).fetchall()
            con.close()
            for row in rows:
                rollout_path = Path(row[0])
                if rollout_path.exists() and rollout_path not in seen:
                    seen.add(rollout_path)
                    rollout_paths.append(rollout_path)
        except sqlite3.Error:
            pass
    if rollout_paths:
        return rollout_paths

    sessions_root = codex_home / "sessions"
    if not sessions_root.exists():
        return []
    paths = sorted(
        sessions_root.rglob("*.jsonl"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return paths[:limit]


def extract_latest_token_count(rollout_path):
    last_payload = None
    last_timestamp = None
    try:
        with rollout_path.open(errors="ignore") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = event.get("payload") or {}
                if event.get("type") == "event_msg" and payload.get("type") == TOKEN_COUNT_TYPE:
                    last_payload = payload
                    last_timestamp = event.get("timestamp")
    except OSError:
        return None
    if not last_payload:
        return None
    return build_usage_snapshot(
        rate_limits=last_payload.get("rate_limits"),
        observed_at=last_timestamp,
        source_rollout_path=str(rollout_path),
    )


def extract_error_message_from_exec_output(stdout_text):
    error_message = None
    for line in stdout_text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "error" and event.get("message"):
            error_message = event["message"]
        if event.get("type") == "turn.failed":
            nested_error = event.get("error") or {}
            if nested_error.get("message"):
                error_message = nested_error["message"]
    return error_message


def run_live_probe(auth_path, workdir, prompt):
    temp_home = Path(tempfile.mkdtemp(prefix="codex-auth-live-"))
    try:
        shutil.copyfile(auth_path, temp_home / "auth.json")
        result = subprocess.run(
            [
                "codex",
                "exec",
                "--json",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                prompt,
            ],
            cwd=workdir,
            env={**os.environ, "CODEX_HOME": str(temp_home)},
            capture_output=True,
            text=True,
            timeout=180,
        )
        session_files = sorted((temp_home / "sessions").rglob("*.jsonl"))
        latest_session = session_files[-1] if session_files else None
        snapshot = extract_latest_token_count(latest_session) if latest_session else None
        error_message = extract_error_message_from_exec_output(result.stdout)
        if snapshot is None:
            snapshot = build_usage_snapshot(
                rate_limits=None,
                observed_at=None,
                source_rollout_path=str(latest_session) if latest_session else None,
                error_message=error_message,
            )
        else:
            snapshot["error_message"] = error_message
            snapshot["retry_after_text"] = extract_retry_after_text(error_message)
            snapshot["limit_hit"] = is_limit_hit_error(error_message)
            snapshot["error_reason_text"] = explain_error_reason(error_message)
            snapshot["plan_type"] = guess_plan_type(
                {
                    "plan_type": snapshot.get("plan_type"),
                    "credits": snapshot.get("credits"),
                    "limit_id": snapshot.get("limit_id"),
                },
                error_message,
            )
            snapshot["command_returncode"] = result.returncode
        snapshot["source"] = "live-probe"
        return snapshot
    finally:
        shutil.rmtree(temp_home, ignore_errors=True)


def find_current_active_snapshot(rollout_paths):
    for rollout_path in rollout_paths:
        snapshot = extract_latest_token_count(rollout_path)
        if snapshot:
            snapshot["source"] = "current-active-session"
            return snapshot
    return None


def find_thread_ids_for_account(codex_home, account_id, limit):
    if not account_id:
        return []
    thread_ids = []
    db_specs = [
        (codex_home / "state_5.sqlite", "logs", "message"),
        (codex_home / "logs_1.sqlite", "logs", "feedback_log_body"),
    ]
    for db_path, table_name, column_name in db_specs:
        if not db_path.exists():
            continue
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            query = (
                f"select thread_id from {table_name} "
                f"where {column_name} like ? and {column_name} like ? "
                f"order by ts desc limit ?"
            )
            rows = cur.execute(
                query,
                (f"{HANDSHAKE_PREFIX}%", f"%chatgpt-account-id: {account_id}%", limit),
            ).fetchall()
            con.close()
        except sqlite3.Error:
            continue
        for row in rows:
            thread_id = row[0]
            if thread_id:
                thread_ids.append(thread_id)
    return unique_preserve_order(thread_ids)


def resolve_rollout_path_for_thread(codex_home, thread_id):
    state_db = codex_home / "state_5.sqlite"
    if not state_db.exists():
        return None
    try:
        con = sqlite3.connect(state_db)
        cur = con.cursor()
        row = cur.execute("select rollout_path from threads where id = ?", (thread_id,)).fetchone()
        con.close()
    except sqlite3.Error:
        return None
    if not row:
        return None
    rollout_path = Path(row[0])
    if rollout_path.exists():
        return rollout_path
    return None


def find_snapshot_by_account(codex_home, account_id, active_account_id, current_snapshot, limit):
    if not account_id:
        return None
    if active_account_id and account_id == active_account_id and current_snapshot:
        snapshot = dict(current_snapshot)
        snapshot["source"] = "current-active-session"
        return snapshot

    for thread_id in find_thread_ids_for_account(codex_home, account_id, limit):
        rollout_path = resolve_rollout_path_for_thread(codex_home, thread_id)
        if not rollout_path:
            continue
        snapshot = extract_latest_token_count(rollout_path)
        if snapshot:
            snapshot["source"] = "latest-account-session"
            snapshot["source_thread_id"] = thread_id
            return snapshot
    return None


def build_profile(path, codex_home, threads_limit, active_account_id, current_snapshot):
    data = load_json(path)
    tokens = data.get("tokens") or {}
    id_payload = decode_jwt_payload(tokens.get("id_token"))
    account_id = tokens.get("account_id")
    selectors = unique_preserve_order(
        [
            *build_selector_variants(path.name, path.stem, profile_alias(path)),
            *build_selector_variants(id_payload.get("email"), account_id),
        ]
    )
    fallback_usage = find_snapshot_by_account(
        codex_home=codex_home,
        account_id=account_id,
        active_account_id=active_account_id,
        current_snapshot=current_snapshot,
        limit=threads_limit,
    )
    return {
        "path": str(path),
        "file": path.name,
        "alias": profile_alias(path),
        "active": path.name == "auth.json",
        "auth_mode": data.get("auth_mode"),
        "last_refresh": data.get("last_refresh"),
        "last_refresh_text": iso_to_local_text(data.get("last_refresh")),
        "account_id": account_id,
        "account_name": id_payload.get("name"),
        "email": id_payload.get("email"),
        "subject": id_payload.get("sub"),
        "selectors": selectors,
        "usage": fallback_usage,
        "_fallback_usage": fallback_usage,
    }


def discover_profiles(codex_home, threads_limit, live=False, workdir=None, live_prompt=DEFAULT_LIVE_PROMPT):
    paths = sorted(path for path in codex_home.glob("auth*.json") if path.is_file())
    rollout_paths = load_recent_rollout_paths(codex_home, threads_limit)
    active_data = load_json(codex_home / "auth.json") if (codex_home / "auth.json").exists() else {}
    active_account_id = (active_data.get("tokens") or {}).get("account_id")
    current_snapshot = find_current_active_snapshot(rollout_paths)
    resolved_workdir = (workdir or Path.cwd()).resolve()
    profiles = []
    if paths:
        max_workers = min(PROFILE_DISCOVERY_MAX_WORKERS, len(paths))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    build_profile,
                    path,
                    codex_home,
                    threads_limit,
                    active_account_id,
                    current_snapshot,
                )
                for path in paths
            ]
            for future in futures:
                profiles.append(future.result())

    if live and profiles:
        max_workers = min(LIVE_PROBE_MAX_WORKERS, len(profiles))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(run_live_probe, Path(profile["path"]), resolved_workdir, live_prompt)
                for profile in profiles
            ]
            for profile, future in zip(profiles, futures):
                fallback_usage = profile.pop("_fallback_usage", None)
                try:
                    usage = future.result()
                except Exception as exc:
                    usage = dict(fallback_usage or {})
                    usage["error_message"] = f"live probe failed: {exc}"
                    usage["error_reason_text"] = "live probe failed"
                if not usage.get("plan_type") and fallback_usage and fallback_usage.get("plan_type"):
                    usage["plan_type"] = fallback_usage["plan_type"]
                profile["usage"] = usage
    else:
        for profile in profiles:
            profile.pop("_fallback_usage", None)

    active_account_ids = {profile["account_id"] for profile in profiles if profile["active"]}
    for profile in profiles:
        profile["same_account_as_active"] = (
            not profile["active"]
            and profile["account_id"] is not None
            and profile["account_id"] in active_account_ids
        )
    profiles.sort(key=lambda item: (not item["active"], item["file"].lower()))
    return profiles


def choose_display_profile(group):
    def priority(profile):
        is_auth_json = profile["file"] == "auth.json"
        return (
            is_auth_json,
            not profile["active"],
            profile["file"].lower(),
        )

    return sorted(group, key=priority)[0]


def profile_identity_key(profile):
    return (
        profile.get("account_id") or "",
        profile.get("subject") or "",
        profile.get("email") or "",
    )


def named_profile_sort_key(profile):
    last_refresh = parse_iso_datetime(profile.get("last_refresh"))
    timestamp = last_refresh.timestamp() if last_refresh else -1
    return (-timestamp, profile["file"].lower())


def files_match(left_path, right_path):
    try:
        return Path(left_path).read_bytes() == Path(right_path).read_bytes()
    except OSError:
        return False


def choose_named_profile_for_active(active_profile, profiles):
    candidates = [profile for profile in profiles if profile["file"] != "auth.json"]
    exact_matches = [
        profile for profile in candidates if files_match(active_profile["path"], profile["path"])
    ]
    if exact_matches:
        return sorted(exact_matches, key=named_profile_sort_key)[0]
    active_identity = profile_identity_key(active_profile)
    if active_identity != ("", "", ""):
        identity_matches = [
            profile for profile in candidates if profile_identity_key(profile) == active_identity
        ]
        if identity_matches:
            return sorted(identity_matches, key=named_profile_sort_key)[0]
    return None


def build_visible_profiles(profiles):
    display_profiles = [dict(profile) for profile in profiles if profile["file"] != "auth.json"]
    for profile in display_profiles:
        profile["active"] = False

    active_profile = next((profile for profile in profiles if profile["file"] == "auth.json"), None)
    if not active_profile:
        display_profiles.sort(key=lambda item: (not item["active"], item["file"].lower()))
        return display_profiles

    chosen_named_profile = choose_named_profile_for_active(active_profile, profiles)
    if not chosen_named_profile:
        fallback_profile = dict(active_profile)
        display_profiles.insert(0, fallback_profile)
        display_profiles.sort(key=lambda item: (not item["active"], item["file"].lower()))
        return display_profiles

    for profile in display_profiles:
        if profile["file"] != chosen_named_profile["file"]:
            continue
        profile["active"] = True
        if active_profile.get("usage"):
            profile["usage"] = active_profile["usage"]
        if active_profile.get("last_refresh"):
            profile["last_refresh"] = active_profile["last_refresh"]
            profile["last_refresh_text"] = active_profile.get("last_refresh_text")
        break

    display_profiles.sort(key=lambda item: (not item["active"], item["file"].lower()))
    return display_profiles


def build_display_profiles(profiles):
    grouped = {}
    for profile in profiles:
        key = (
            profile.get("account_id") or "",
            profile.get("subject") or "",
            profile.get("email") or "",
        )
        if key == ("", "", ""):
            key = profile["file"]
        grouped.setdefault(key, []).append(profile)

    display_profiles = []
    for group in grouped.values():
        chosen = choose_display_profile(group)
        active = any(profile["active"] for profile in group)
        chosen_usage = chosen.get("usage")
        active_profile = next((profile for profile in group if profile["active"]), None)
        if active_profile and active_profile.get("usage"):
            chosen_usage = active_profile["usage"]
        display_profile = dict(chosen)
        display_profile["active"] = active
        display_profile["usage"] = chosen_usage
        display_profile["has_duplicate_files"] = len(group) > 1
        display_profile["duplicate_files"] = [profile["file"] for profile in group]
        display_profiles.append(display_profile)

    display_profiles.sort(key=lambda item: (not item["active"], item["file"].lower()))
    return display_profiles


def format_window_label(minutes):
    if minutes == 300:
        return "5h"
    if minutes == 10080:
        return "7d"
    if not minutes:
        return "unknown"
    if minutes % 1440 == 0:
        return f"{minutes // 1440}d"
    if minutes % 60 == 0:
        return f"{minutes // 60}h"
    return f"{minutes}m"


def format_percent(value):
    if value is None:
        return "?"
    if int(value) == value:
        return str(int(value))
    return f"{value:.1f}".rstrip("0").rstrip(".")


def make_emoji_bar(percent, width=10):
    if percent is None:
        return "❔" * width
    clamped = max(0.0, min(100.0, float(percent)))
    filled = int(round((clamped / 100.0) * width))
    return ("🟩" * filled) + ("⬜" * (width - filled))


def format_limit_segment(icon, label, percent):
    return f"{icon} {label} left: {make_emoji_bar(percent)} {format_percent(percent)}%"


def build_weekly_reset_label(usage):
    weekly_reset_text = usage.get("secondary_resets_at_pretty_text")
    if not weekly_reset_text and usage.get("retry_after_text"):
        weekly_reset_text = human_time_to_pretty_local_text(usage["retry_after_text"])
    return f"🔁 7d reset: {weekly_reset_text or 'unknown'}"


def build_status_label(profile):
    usage = profile.get("usage") or {}
    error_reason = usage.get("error_reason_text")
    if error_reason == "request blocked":
        return "🚫 ACTIVE BLOCKED" if profile["active"] else "🚫 BLOCKED"
    if error_reason in {"refresh token already used", "login expired", "login invalid"}:
        return "🔴 EXPIRED"
    if usage.get("limit_hit"):
        return "⛔ ACTIVE USAGE LIMIT" if profile["active"] else "⛔ USAGE LIMIT"
    if profile["active"]:
        return "🟢 ACTIVE"
    return "⚪ INACTIVE"


def display_width(text):
    if wcswidth is not None:
        width = wcswidth(text)
        if width >= 0:
            return width
    return len(text)


def pad_display(text, width):
    padding = max(0, width - display_width(text))
    return text + (" " * padding)


def build_profile_columns(profile, header_timestamp):
    usage = profile.get("usage") or {}
    status_label = f"({build_status_label(profile)})"
    file_label = f"📄 {profile['file']}"
    name_label = f"👤 {profile.get('account_name') or 'unknown'}"
    plan_label = f"📦 {usage.get('plan_type') or 'unknown'}"
    primary_remaining = usage.get("primary_remaining_percent")
    secondary_remaining = usage.get("secondary_remaining_percent")
    if usage.get("limit_hit"):
        if primary_remaining is None:
            primary_remaining = 0.0
        if secondary_remaining is None:
            secondary_remaining = 0.0
    five_hour_label = format_limit_segment("⏱️", "5h", primary_remaining)
    seven_day_label = format_limit_segment("📅", "7d", secondary_remaining)
    weekly_reset_label = build_weekly_reset_label(usage)
    warning_label = f"⚠️ {usage['error_reason_text']}" if usage.get("error_reason_text") else None
    segments = [file_label, status_label, name_label, plan_label, five_hour_label, seven_day_label, weekly_reset_label]
    if profile.get("last_refresh_text"):
        segments.append(f"🔄 last refresh {profile['last_refresh_text']}")
    if warning_label:
        segments.append(warning_label)
    if usage.get("retry_after_text") and usage.get("secondary_resets_at_pretty_text"):
        segments.append(f"🕒 retry after {usage['retry_after_text']}")
    observed_at = usage.get("observed_at")
    if observed_at and usage.get("source") != "live-probe" and observed_at != header_timestamp:
        pretty_snapshot = iso_to_pretty_local_text(observed_at)
        segments.append(f"🕒 {pretty_snapshot or 'unknown'}")
    return segments


def pick_status_timestamp(profiles):
    active_profiles = [profile for profile in profiles if profile["active"] and profile.get("usage")]
    if active_profiles:
        return active_profiles[0]["usage"].get("observed_at")
    for profile in profiles:
        usage = profile.get("usage")
        if usage and usage.get("observed_at"):
            return usage.get("observed_at")
    return None


def print_profiles(profiles):
    display_profiles = build_visible_profiles(profiles)
    status_timestamp = pick_status_timestamp(display_profiles)
    if status_timestamp:
        print(iso_to_pretty_local_text(status_timestamp))
    rows = [build_profile_columns(profile, status_timestamp) for profile in display_profiles]
    widths = []
    for index in range(BASE_TABLE_COLUMN_COUNT):
        widths.append(
            max(
                BASE_TABLE_MIN_WIDTHS[index],
                max(display_width(row[index]) for row in rows),
            )
        )
    for row in rows:
        padded = [pad_display(row[index], widths[index]) for index in range(BASE_TABLE_COLUMN_COUNT)]
        if len(row) > BASE_TABLE_COLUMN_COUNT:
            padded.extend(row[BASE_TABLE_COLUMN_COUNT:])
        print(TABLE_SEPARATOR.join(padded))


def resolve_profile(profiles, selector):
    normalized = selector.strip().lower()
    matches = [profile for profile in profiles if normalized in profile["selectors"]]
    if not matches:
        raise ValueError(f"No auth profile matched '{selector}'.")
    if len(matches) > 1:
        options = ", ".join(profile["file"] for profile in matches)
        raise ValueError(
            f"Selector '{selector}' is ambiguous. Use one of these file names: {options}"
        )
    return matches[0]


def command_list(args):
    profiles = discover_profiles(
        codex_home=args.codex_home,
        threads_limit=args.threads_limit,
        live=args.live,
        workdir=args.workdir,
        live_prompt=args.live_prompt,
    )
    output = {"codex_home": str(args.codex_home), "profiles": profiles}
    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return
    print_profiles(profiles)


def command_switch(args):
    profiles = discover_profiles(args.codex_home, args.threads_limit)
    profile = resolve_profile(profiles, args.selector)
    source = Path(profile["path"])
    destination = args.codex_home / "auth.json"
    if args.dry_run:
        print(f"Would copy {source.name} to {destination}")
        return
    if source.resolve() == destination.resolve():
        print(f"{source.name} is already the active auth.json")
        return
    shutil.copyfile(source, destination)
    print(f"Copied {source.name} to {destination}")


def command_add_account(args):
    if args.login and args.source:
        raise ValueError("Use either --login or --source, not both together.")

    if args.login:
        print("Starting `codex login`. Sign into the account you want to back up, then this command will save the new auth.json.")
        subprocess.run(["codex", "login"], check=True)

    source = args.source.expanduser().resolve() if args.source else (args.codex_home / "auth.json")
    if not source.exists():
        raise ValueError(f"Source auth file not found: {source}")
    if not source.is_file():
        raise ValueError(f"Source path is not a file: {source}")

    target = args.codex_home / normalize_backup_filename(args.name)
    if source.resolve() == target.resolve():
        raise ValueError("Source and target are the same file.")

    if target.exists():
        if not args.force:
            raise ValueError(
                f"Backup file already exists: {target.name}. Use --force to overwrite it."
            )
        if not target.is_file():
            raise ValueError(f"Backup target is not a file: {target}")

    if args.dry_run:
        print(f"Would copy {source} to {target}")
        return

    shutil.copyfile(source, target)
    print(f"Saved backup: {target}")


def build_parser():
    parser = argparse.ArgumentParser(description="Inspect and switch saved Codex auth profiles.")
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path.home() / ".codex",
        help="Path to the Codex home directory (default: ~/.codex)",
    )
    parser.add_argument(
        "--threads-limit",
        type=int,
        default=800,
        help="How many recent threads to inspect for usage snapshots",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List saved auth profiles")
    list_parser.add_argument("--json", action="store_true", help="Emit JSON output")
    list_parser.add_argument(
        "--live",
        action="store_true",
        help="Probe each auth file with an isolated Codex request for current limits",
    )
    list_parser.add_argument(
        "--workdir",
        type=Path,
        default=Path.cwd(),
        help="Working directory to use for live Codex probes (default: current directory)",
    )
    list_parser.add_argument(
        "--live-prompt",
        default=DEFAULT_LIVE_PROMPT,
        help="Tiny prompt to send during live Codex probes",
    )
    list_parser.set_defaults(func=command_list)

    switch_parser = subparsers.add_parser("switch", help="Copy one auth profile to auth.json")
    switch_parser.add_argument("selector", help="File name, alias, email, or account ID")
    switch_parser.add_argument("--dry-run", action="store_true", help="Show the copy without doing it")
    switch_parser.set_defaults(func=command_switch)

    add_parser = subparsers.add_parser(
        "add-account",
        help="Back up the current auth.json or another auth file into ~/.codex/auth_<name>.json",
    )
    add_parser.add_argument("name", help="Backup name, for example 'ben', 'team', or 'work'")
    add_parser.add_argument(
        "--source",
        type=Path,
        help="Optional auth file to import instead of ~/.codex/auth.json",
    )
    add_parser.add_argument(
        "--login",
        action="store_true",
        help="Run `codex login` first, then back up the resulting auth.json",
    )
    add_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the backup file if it already exists",
    )
    add_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the copy without doing it",
    )
    add_parser.set_defaults(func=command_add_account)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.codex_home = args.codex_home.expanduser().resolve()
    if hasattr(args, "workdir") and isinstance(args.workdir, Path):
        args.workdir = args.workdir.expanduser().resolve()
    if not args.codex_home.exists():
        print(f"Codex home not found: {args.codex_home}", file=sys.stderr)
        sys.exit(1)
    try:
        args.func(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
