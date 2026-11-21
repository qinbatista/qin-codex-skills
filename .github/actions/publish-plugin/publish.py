"""Publish the native Skill marketplace on the source repository's primary history."""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath


sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "management-skill" / "scripts"))
from install_skill_pack import PACKS, skill_file


SOURCE_REF = "refs/heads/master"
PACKAGE_REF = "refs/tags/codex/plugin"
MARKETPLACE = ".agents/plugins/marketplace.json"


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


def write_tree(project, files):
    directories = defaultdict(dict)
    records = []
    for path, (mode, oid) in sorted(files.items()):
        name, separator, remainder = path.partition("/")
        if separator:
            directories[name][remainder] = mode, oid
        else:
            kind = "commit" if mode == "160000" else "blob"
            records.append(f"{mode} {kind} {oid}\t{name}\0")
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


def primary_tree(project, package):
    prefix = f"plugins/{package['name']}/skills/"
    source = source_entries(project, package["sourceCommit"])
    files = {path: entry for path, entry in source.items() if not path.startswith(prefix)}
    files.update(source_entries(project, package["tree"]))
    return write_tree(project, files)


def prepare(project, name):
    """Stage the native layout alongside the currently staged Skill sources."""
    paths = [MARKETPLACE, f"plugins/{name}/skills"]
    if git(project, "diff", "--name-only", "--", *paths) or git(
        project, "ls-files", "--others", "--exclude-standard", "--", *paths
    ):
        raise ValueError("The generated marketplace paths contain local edits. Review them before preparing the package.")
    index_tree = git_text(project, "write-tree")
    package = build_package(project, index_tree, name)
    tree = primary_tree(project, package)
    if tree != index_tree:
        git(project, "restore", f"--source={tree}", "--staged", "--worktree", "--", *paths)
    return {"status": "prepared", "skills": package["skills"], "tree": tree}


def publish(project, package):
    source = package["sourceCommit"]
    if remote_ref(project, SOURCE_REF) != source:
        print("This run is no longer for the current master commit. The current run owns publication.")
        return {"status": "superseded"}

    previous = remote_ref(project, PACKAGE_REF)
    tree = primary_tree(project, package)
    commit = source
    if tree != git_text(project, "rev-parse", f"{source}^{{tree}}"):
        # Direct source pushes may omit the generated layout. Keep their full tree and history.
        commit = git_text(project, "commit-tree", tree, "-p", source, "-m", f"Refresh {package['name']} marketplace files")
    if previous == commit and source == commit:
        return {"status": "current", "commit": commit}
    git(project, "push", "--atomic", f"--force-with-lease={SOURCE_REF}:{source}",
        f"--force-with-lease={PACKAGE_REF}:{previous or ''}", "origin",
        f"{commit}:{SOURCE_REF}", f"{commit}:{PACKAGE_REF}")
    current_primary = remote_ref(project, SOURCE_REF)
    if current_primary != commit:
        return {"status": "superseded"}
    if remote_ref(project, PACKAGE_REF) != commit:
        raise RuntimeError("The package tag and the published master do not identify the same commit.")
    return {"status": "published", "commit": commit}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--plugin", choices=PACKS, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--prepare", action="store_true", help="Stage the distribution layout from the Git index in the source commit")
    parser.add_argument("--archive", type=Path, help="Write a skills-only release ZIP for the grouped installer")
    args = parser.parse_args()
    project = args.project_root.resolve()
    try:
        if args.prepare:
            print(json.dumps(prepare(project, args.plugin), indent=2))
            return
        source = git_text(project, "rev-parse", "HEAD^{commit}")
        package = build_package(project, source, args.plugin)
        if args.publish:
            package.update(publish(project, package))
        if args.archive and package.get("status") != "superseded":
            git(project, "archive", "--format=zip", f"--prefix={args.plugin}/",
                f"--output={args.archive.resolve()}", package["tree"])
        print(json.dumps(package, indent=2))
    except subprocess.CalledProcessError as error:
        parser.exit(1, error.stderr.decode("utf-8", "replace"))
    except (KeyError, TypeError, ValueError, RuntimeError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
