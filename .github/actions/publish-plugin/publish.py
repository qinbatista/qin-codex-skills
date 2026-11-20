"""Publish a Git marketplace containing the selected plugin's Skill files."""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath


sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


SOURCE_REF = "refs/heads/master"
PACKAGE_REF = "refs/heads/codex/plugin"
MARKETPLACE = ".agents/plugins/marketplace.json"
SKILL_FOLDERS = {"agents", "assets", "references", "scripts"}
OMITTED_NAMES = {"agents.md", "ai-index", "cache", "local", "readme", "test", "tests", "__pycache__"}


def git(project, *args, content=None):
    result = subprocess.run(
        ["git", *args], cwd=project, input=content, capture_output=True, check=True,
        **hidden_process_options(),
    )
    return result.stdout


def git_text(project, *args, content=None):
    return git(project, *args, content=content).decode("utf-8").strip()


def source_entries(project, source):
    entries = {}
    for record in git(project, "ls-tree", "-r", "-z", "--full-tree", source).split(b"\0"):
        if record:
            metadata, filename = record.split(b"\t", 1)
            mode, _, oid = metadata.decode("ascii").split()
            entries[filename.decode("utf-8")] = mode, oid
    return entries


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


def write_tree(project, files):
    directories = defaultdict(dict)
    records = []
    for path, (mode, oid) in sorted(files.items()):
        name, separator, remainder = path.partition("/")
        if separator:
            directories[name][remainder] = mode, oid
        else:
            records.append(f"{mode} blob {oid}\t{name}\0")
    for name, children in sorted(directories.items()):
        oid = write_tree(project, children)
        records.append(f"040000 tree {oid}\t{name}\0")
    return git_text(project, "mktree", "-z", content="".join(records).encode("utf-8"))


def build_package(project, source, name):
    package = f"plugins/{name}"
    manifest_path = f"{package}/plugin.json"
    entries = source_entries(project, source)
    manifest = json.loads(git(project, "show", f"{source}:{manifest_path}"))
    skills = json.loads(git(project, "show", f"{source}:{package}/skills.json"))
    if manifest.get("name") != name or not re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")):
        raise ValueError("The plugin manifest needs the selected name and a semantic version.")
    if not isinstance(skills, list) or not skills or any(
        not isinstance(skill, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*-skill", skill) for skill in skills
    ) or len(skills) != len(set(skills)):
        raise ValueError("The Skill list needs unique source folder names.")

    files = {manifest_path: entries[manifest_path]}
    for skill in skills:
        prefix = f"{skill}/"
        if f"{prefix}SKILL.md" not in entries:
            raise ValueError(f"Missing tracked Skill entry for {skill}.")
        for path, entry in entries.items():
            if path.startswith(prefix) and skill_file(PurePosixPath(path[len(prefix):])):
                files[f"{package}/skills/{path}"] = entry
    for path, (mode, _) in files.items():
        if mode not in {"100644", "100755"}:
            raise ValueError(f"Plugin package file must be a tracked regular file: {path}")

    interface = manifest["extensions"]["com.openai"]["interface"]
    catalog = {
        "name": name,
        "interface": {"displayName": interface["displayName"]},
        "plugins": [{
            "name": name,
            "source": {"source": "local", "path": f"./{package}"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": interface["category"],
        }],
    }
    content = (json.dumps(catalog, indent=2) + "\n").encode("utf-8")
    files[MARKETPLACE] = "100644", git_text(project, "hash-object", "-w", "--stdin", content=content)
    return {"name": name, "sourceCommit": source, "tree": write_tree(project, files), "skills": skills, "fileCount": len(files)}


def remote_ref(project, ref):
    line = git_text(project, "ls-remote", "--refs", "origin", ref)
    return line.split("\t", 1)[0] if line else None


def publish(project, package):
    source = package["sourceCommit"]
    if remote_ref(project, SOURCE_REF) != source:
        print("This run is no longer for the current master commit. The current run owns publication.")
        return {"status": "superseded"}

    previous = remote_ref(project, PACKAGE_REF)
    parents = []
    if previous:
        git(project, "fetch", "--no-tags", "origin", PACKAGE_REF)
        if git_text(project, "rev-parse", "FETCH_HEAD") != previous:
            raise RuntimeError("The plugin branch changed during fetch. Retry against the current branch.")
        if git_text(project, "rev-parse", f"{previous}^{{tree}}") == package["tree"]:
            return {"status": "current", "commit": previous}
        parents = ["-p", previous]

    commit = git_text(
        project, "commit-tree", package["tree"], *parents,
        "-m", f"Publish {package['name']}", "-m", f"Source commit {source}",
    )
    if remote_ref(project, SOURCE_REF) != source:
        return {"status": "superseded"}
    git(project, "push", "origin", f"{commit}:{PACKAGE_REF}")
    if remote_ref(project, PACKAGE_REF) != commit:
        raise RuntimeError("The freshly read plugin branch does not match the published commit.")
    return {"status": "published", "commit": commit}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--plugin", choices=("qin-codex-skills", "qin-unity-skills"), required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    project = args.project_root.resolve()
    try:
        source = git_text(project, "rev-parse", "HEAD^{commit}")
        package = build_package(project, source, args.plugin)
        if args.publish:
            package.update(publish(project, package))
        print(json.dumps(package, indent=2))
    except subprocess.CalledProcessError as error:
        parser.exit(1, error.stderr.decode("utf-8", "replace"))
    except (KeyError, TypeError, ValueError, RuntimeError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
