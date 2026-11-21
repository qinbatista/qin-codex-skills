"""Install a published Qin Skill pack into one user-global directory."""

import argparse
import io
import json
import re
import shutil
import stat
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


PACKS = ("qin-codex-skills", "qin-unity-skills")
RELEASE = "https://github.com/qinbatista/{pack}/releases/download/codex%2Fplugin/{pack}.zip"
TAG_ARCHIVE = "https://codeload.github.com/qinbatista/{pack}/zip/codex/plugin"
SKILL_FOLDERS = {"agents", "assets", "references", "scripts"}
OMITTED_NAMES = {"agents.md", "ai-index", "cache", "local", "readme", "test", "tests", "__pycache__"}
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024


def skill_file(relative):
    if relative.parts == ("SKILL.md",):
        return True
    if len(relative.parts) < 2 or relative.parts[0] not in SKILL_FOLDERS:
        return False
    for part in relative.parts[1:]:
        name = part.casefold()
        if name in OMITTED_NAMES or name.startswith((".", "readme.", "github-readme-template")):
            return False
    return relative.suffix.casefold() not in {".pyc", ".pyo", ".log"}


def fetch_pack(pack):
    try:
        response = urllib.request.urlopen(RELEASE.format(pack=pack), timeout=40)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        error.close()
        response = urllib.request.urlopen(TAG_ARCHIVE.format(pack=pack), timeout=40)
    with response:
        archive = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(archive) > MAX_ARCHIVE_BYTES:
        raise ValueError("The downloaded package exceeds the supported size.")
    return archive


def package_files(archive, pack):
    files = {}
    seen = set()
    size = 0
    with zipfile.ZipFile(io.BytesIO(archive)) as release:
        for item in release.infolist():
            parts = item.filename.split("/")
            if item.is_dir() or parts[1:3] != ["plugins", pack]:
                continue
            relative = parts[3:]
            if relative == ["plugin.json"]:
                target = PurePosixPath("plugin.json")
            elif len(relative) >= 3 and relative[0] == "skills" and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*-skill", relative[1]):
                if not skill_file(PurePosixPath(*relative[2:])):
                    continue
                target = PurePosixPath(*relative[1:])
            else:
                continue
            mode = item.external_attr >> 16
            key = target.as_posix().casefold()
            if any(part in {"", ".", ".."} or "\\" in part or ":" in part for part in relative):
                raise ValueError(f"Invalid package path: {item.filename}")
            if stat.S_IFMT(mode) not in {0, stat.S_IFREG} or key in seen:
                raise ValueError(f"Invalid package file: {item.filename}")
            size += item.file_size
            if size > MAX_ARCHIVE_BYTES:
                raise ValueError("The expanded package exceeds the supported size.")
            seen.add(key)
            files[target] = release.read(item), mode

    manifest = files.get(PurePosixPath("plugin.json"))
    folders = {path.parts[0] for path in files if len(path.parts) > 1}
    if manifest is None or not matches_manifest(manifest[0], pack):
        raise ValueError("The archive does not contain the selected plugin manifest.")
    if not folders or any(PurePosixPath(folder, "SKILL.md") not in files for folder in folders):
        raise ValueError("The archive is missing a Skill entry.")
    return files


def real_directory(directory):
    info = directory.lstat()
    attributes = getattr(info, "st_file_attributes", 0)
    return stat.S_ISDIR(info.st_mode) and not (attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def matches_manifest(contents, pack):
    metadata = json.loads(contents)
    return isinstance(metadata, dict) and metadata.get("name") == pack


def require_group(destination, pack):
    try:
        if not real_directory(destination):
            raise ValueError(f"Expected a regular package directory: {destination}")
    except FileNotFoundError:
        return False
    manifest = destination / "plugin.json"
    if not manifest.is_file() or manifest.is_symlink() or not matches_manifest(manifest.read_bytes(), pack):
        raise ValueError(f"This directory does not belong to {pack}: {destination}")
    return True


def apply_pack(root, pack, files, scratch=None):
    if pack not in PACKS:
        raise ValueError(f"Unknown Skill pack: {pack}")
    try:
        parent_is_directory = real_directory(root.parent)
    except FileNotFoundError:
        if files is None:
            return root / pack
        root.parent.mkdir(parents=True, exist_ok=True)
        parent_is_directory = real_directory(root.parent)
    if not parent_is_directory:
        raise ValueError(f"Expected a regular parent directory: {root.parent}")
    if files is not None:
        root.mkdir(exist_ok=True)
    try:
        root_is_directory = real_directory(root)
    except FileNotFoundError:
        return root / pack
    if not root_is_directory:
        raise ValueError(f"Expected a regular Skills root: {root}")
    destination = root / pack
    lock = root / f".{pack}.install-lock"
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise ValueError(f"Another operation owns this Skill pack: {lock}") from error

    try:
        installed = require_group(destination, pack)
        if files is None:
            if installed:
                shutil.rmtree(destination)
            return destination

        stage_parent = scratch or root
        if not real_directory(stage_parent) or stage_parent.stat().st_dev != root.stat().st_dev:
            raise ValueError("The staging directory must be on the same volume as the Skills directory.")
        stage = Path(tempfile.mkdtemp(prefix=f".{pack}-", dir=stage_parent))
        incoming = stage / "incoming"
        previous = stage / "previous"
        try:
            for relative, (contents, mode) in files.items():
                target = incoming.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(contents)
                target.chmod(0o755 if mode & 0o111 else 0o644)
            if installed:
                destination.rename(previous)
            incoming.rename(destination)
        finally:
            if previous.exists() and not destination.exists():
                previous.rename(destination)
            shutil.rmtree(stage)
        return destination
    finally:
        lock.rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "update", "uninstall"))
    parser.add_argument("pack", choices=PACKS)
    parser.add_argument("--staging-dir", type=Path, help="Existing scratch directory on the installation volume")
    args = parser.parse_args()
    try:
        files = None if args.action == "uninstall" else package_files(fetch_pack(args.pack), args.pack)
        location = apply_pack(Path.home().resolve() / ".agents" / "skills", args.pack, files, args.staging_dir)
    except (OSError, ValueError, TypeError, zipfile.BadZipFile) as error:
        parser.exit(1, f"{error}\n")
    print(f"{'Removed' if files is None else 'Installed'} {location}")


if __name__ == "__main__":
    main()
