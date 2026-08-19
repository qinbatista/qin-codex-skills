#!/usr/bin/env python3
"""Resolve and inspect Codex runtime SQLite files without assuming one version."""

import os
import re
import sqlite3
from pathlib import Path


# Codex has used numbered state files, but an isolated runtime may add a
# descriptive suffix before a formal schema version is assigned.  Match only
# state databases (never WAL/journal sidecars), then validate the schema below.
STATE_DATABASE_PATTERN = re.compile(r"^state(?:[_-]([A-Za-z0-9][A-Za-z0-9._-]*))?\.sqlite$")
THREAD_REQUIRED_COLUMNS = frozenset({"id"})
THREAD_OPTIONAL_COLUMNS = ("rollout_path", "model", "reasoning_effort", "tokens_used", "cli_version", "model_provider", "source")


class CodexSQLiteResolutionError(ValueError):
    """Raised when a configured runtime database is absent or incompatible."""


def _runtime_roots(sqlite_home=None, environment=None):
    values = environment if environment is not None else os.environ
    roots = []
    for value in (sqlite_home, values.get("CODEX_SQLITE_HOME"), values.get("CODEX_HOME"), Path.home() / ".codex"):
        if value is None:
            continue
        root = Path(value).expanduser()
        if root not in roots:
            roots.append(root)
    return roots


def _candidate_sort_key(path):
    match = STATE_DATABASE_PATTERN.fullmatch(path.name)
    suffix = match.group(1) if match else ""
    numeric_version = tuple(int(value) for value in re.findall(r"\d+", suffix or ""))
    try:
        modified_ns = path.stat().st_mtime_ns
    except OSError:
        modified_ns = -1
    # Prefer an explicit numeric schema suffix (state_6) over an unversioned
    # or descriptive candidate, then use modification time as a deterministic
    # tie-breaker for future state_*.sqlite forms.
    return bool(numeric_version), numeric_version, modified_ns, path.name


def _discover_candidates(root):
    if root.is_file():
        return [root]
    if not root.is_dir():
        return []
    return sorted((path for path in root.iterdir() if path.is_file() and STATE_DATABASE_PATTERN.fullmatch(path.name)), key=_candidate_sort_key, reverse=True)


def inspect_threads_schema(database_path):
    """Return table/column capabilities using a read-only SQLite connection."""
    path = Path(database_path).expanduser().resolve()
    if not path.is_file():
        raise CodexSQLiteResolutionError(f"Codex runtime database does not exist: {path}")
    connection = None
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        table_names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        columns = {row[1] for row in connection.execute("PRAGMA table_info(threads)")} if "threads" in table_names else set()
    except sqlite3.Error as error:
        raise CodexSQLiteResolutionError(f"Codex runtime database is unreadable: {type(error).__name__}") from error
    finally:
        if connection is not None:
            connection.close()
    return {"path": path, "tables": table_names, "threads_columns": columns, "threads_compatible": "threads" in table_names and THREAD_REQUIRED_COLUMNS.issubset(columns)}


def resolve_codex_sqlite_db(explicit_db=None, sqlite_home=None, environment=None, require_compatible=True, strict_sqlite_home=False):
    """Resolve the newest schema-compatible runtime database by documented precedence."""
    values = environment if environment is not None else os.environ
    configured_database = explicit_db if explicit_db is not None else values.get("CODEX_SQLITE_DB")
    if configured_database:
        candidates = _discover_candidates(Path(configured_database).expanduser())
        if not candidates:
            raise CodexSQLiteResolutionError("configured Codex runtime database was not found")
        for candidate in candidates:
            try:
                capabilities = inspect_threads_schema(candidate)
            except CodexSQLiteResolutionError:
                continue
            if not require_compatible or capabilities["threads_compatible"]:
                return capabilities["path"]
        raise CodexSQLiteResolutionError("configured Codex runtime database lacks a compatible threads table")
    roots = [Path(sqlite_home).expanduser()] if strict_sqlite_home and sqlite_home is not None else _runtime_roots(sqlite_home, values)
    for root in roots:
        for candidate in _discover_candidates(root):
            try:
                capabilities = inspect_threads_schema(candidate)
            except CodexSQLiteResolutionError:
                # Discovery may encounter a partially-written or obsolete
                # database.  It is not a candidate until its schema validates.
                continue
            if not require_compatible or capabilities["threads_compatible"]:
                return capabilities["path"]
    return None


def thread_column_capabilities(database_path):
    """Return readable thread columns, allowing callers to degrade optional metadata."""
    capabilities = inspect_threads_schema(database_path)
    if not capabilities["threads_compatible"]:
        raise CodexSQLiteResolutionError("Codex runtime database lacks required threads.id capability")
    available = capabilities["threads_columns"]
    return {"path": capabilities["path"], "available": tuple(column for column in THREAD_OPTIONAL_COLUMNS if column in available), "missing": tuple(column for column in THREAD_OPTIONAL_COLUMNS if column not in available)}
