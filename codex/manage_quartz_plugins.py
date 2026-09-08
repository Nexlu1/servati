#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


EXPECTED_QUARTZ_SHA = "f1fba3fc55cbf60a60a5d09c95a49c042cdab63a"
EXPECTED_PLUGIN_COUNT = 26
LOCAL_SOURCE_PREFIX = "./plugin-sources/"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SOURCE_PATTERN = re.compile(r"^\s*-\s+source:\s*[\"']?([^\"'#\s]+)", re.MULTILINE)


def run_git(*args: str, cwd: Path | None = None, capture: bool = False) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def load_specs(manifest_path: Path, config_path: Path) -> list[dict[str, str]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = manifest.get("sources", [])
    engines = [source for source in sources if source.get("role") == "engine"]
    if len(engines) != 1 or engines[0].get("sha") != EXPECTED_QUARTZ_SHA:
        raise SystemExit(f"Manifest must pin Quartz at {EXPECTED_QUARTZ_SHA}")

    plugins: dict[str, dict[str, str]] = {}
    required_names: set[str] = set()
    for source in sources:
        if source.get("role") == "engine":
            continue
        repo = source.get("repo", "")
        sha = source.get("sha", "")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise SystemExit(f"Invalid GitHub repository in manifest: {repo!r}")
        if not SHA_PATTERN.fullmatch(sha):
            raise SystemExit(f"Invalid exact Git SHA for {repo}: {sha!r}")
        name = repo.rsplit("/", 1)[1]
        if name in plugins:
            raise SystemExit(f"Duplicate plugin repository basename in manifest: {name}")
        plugins[name] = {"name": name, "repo": repo, "sha": sha}
        if source.get("role") == "required":
            required_names.add(name)

    configured_sources = SOURCE_PATTERN.findall(config_path.read_text(encoding="utf-8"))
    if len(configured_sources) != EXPECTED_PLUGIN_COUNT:
        raise SystemExit(
            f"Expected {EXPECTED_PLUGIN_COUNT} configured plugins, found {len(configured_sources)}"
        )

    configured_names: list[str] = []
    for source in configured_sources:
        if not source.startswith(LOCAL_SOURCE_PREFIX):
            raise SystemExit(f"Plugin source is not a supported local path: {source}")
        name = source.removeprefix(LOCAL_SOURCE_PREFIX)
        if not name or "/" in name or "\\" in name:
            raise SystemExit(f"Plugin source must name one local plugin directory: {source}")
        if name in configured_names:
            raise SystemExit(f"Duplicate configured plugin: {name}")
        if name not in plugins:
            raise SystemExit(f"Configured plugin has no exact manifest pin: {name}")
        configured_names.append(name)

    missing_required = sorted(required_names - set(configured_names))
    if missing_required:
        raise SystemExit(f"Required manifest plugins missing from config: {', '.join(missing_required)}")
    return [plugins[name] for name in configured_names]


def write_result(path: Path, operation: str, plugins: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "operation": operation,
                "quartz_sha": EXPECTED_QUARTZ_SHA,
                "plugin_count": len(plugins),
                "plugins": plugins,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def acquire(specs: list[dict[str, str]], output: Path, result_path: Path) -> None:
    marker = output / ".servati_generated_plugins"
    if output.exists():
        if not marker.exists():
            raise SystemExit(f"Refusing to replace non-generated plugin directory: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    marker.write_text("generated\n", encoding="utf-8")

    verified = []
    for spec in specs:
        plugin_dir = output / spec["name"]
        url = f"https://github.com/{spec['repo']}.git"
        print(f"Acquiring {spec['repo']}@{spec['sha']}", flush=True)
        run_git("init", "--quiet", str(plugin_dir))
        run_git("remote", "add", "origin", url, cwd=plugin_dir)
        run_git("fetch", "--quiet", "--depth=1", "--no-tags", "origin", spec["sha"], cwd=plugin_dir)
        run_git("checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=plugin_dir)
        actual_sha = run_git("rev-parse", "HEAD", cwd=plugin_dir, capture=True)
        actual_url = run_git("remote", "get-url", "origin", cwd=plugin_dir, capture=True)
        status = run_git("status", "--porcelain", cwd=plugin_dir, capture=True)
        if actual_sha != spec["sha"]:
            raise SystemExit(f"SHA mismatch for {spec['repo']}: {actual_sha}")
        if actual_url != url:
            raise SystemExit(f"Origin mismatch for {spec['repo']}: {actual_url}")
        if status:
            raise SystemExit(f"Fresh checkout is dirty for {spec['repo']}: {status}")
        verified.append({**spec, "actual_sha": actual_sha, "origin": actual_url})

    write_result(result_path, "acquire", verified)
    print(f"Acquired and verified {len(verified)} exact plugin revisions", flush=True)


def verify(
    specs: list[dict[str, str]], source_root: Path, installed_root: Path, result_path: Path
) -> None:
    lockfile_path = installed_root.parent.parent / "quartz.lock.json"
    lockfile = json.loads(lockfile_path.read_text(encoding="utf-8"))
    lock_plugins = lockfile.get("plugins", {})
    expected_names = {spec["name"] for spec in specs}
    if set(lock_plugins) != expected_names:
        missing = sorted(expected_names - set(lock_plugins))
        extra = sorted(set(lock_plugins) - expected_names)
        raise SystemExit(f"Plugin lock mismatch; missing={missing}, extra={extra}")

    verified = []
    for spec in specs:
        source_dir = source_root / spec["name"]
        installed_dir = installed_root / spec["name"]
        required_files = ["package.json", "dist/index.js", "dist/index.d.ts"]
        missing_files = [name for name in required_files if not (installed_dir / name).is_file()]
        if missing_files:
            raise SystemExit(f"Plugin {spec['name']} is not built: {', '.join(missing_files)}")
        if not installed_dir.is_symlink() or installed_dir.resolve() != source_dir.resolve():
            raise SystemExit(f"Plugin {spec['name']} is not linked to its acquired exact-SHA source")
        source_sha = run_git("rev-parse", "HEAD", cwd=source_dir, capture=True)
        installed_sha = run_git("rev-parse", "HEAD", cwd=installed_dir, capture=True)
        actual_url = run_git("remote", "get-url", "origin", cwd=source_dir, capture=True)
        tracked_changes = run_git(
            "status", "--porcelain", "--untracked-files=no", cwd=source_dir, capture=True
        )
        expected_url = f"https://github.com/{spec['repo']}.git"
        if source_sha != spec["sha"] or installed_sha != spec["sha"]:
            raise SystemExit(
                f"Installed SHA mismatch for {spec['name']}: source={source_sha}, installed={installed_sha}"
            )
        if actual_url != expected_url:
            raise SystemExit(f"Origin mismatch for {spec['name']}: {actual_url}")
        if tracked_changes:
            raise SystemExit(f"Plugin {spec['name']} has modified tracked files: {tracked_changes}")
        lock_entry = lock_plugins[spec["name"]]
        expected_source = f"{LOCAL_SOURCE_PREFIX}{spec['name']}"
        if (
            lock_entry.get("commit") != "local"
            or lock_entry.get("source") != expected_source
            or Path(lock_entry.get("resolved", "")).resolve() != source_dir.resolve()
        ):
            raise SystemExit(f"Plugin {spec['name']} was not installed through Quartz local loading")
        verified.append(
            {
                **spec,
                "actual_sha": installed_sha,
                "origin": actual_url,
                "built": True,
                "load_mode": "local",
            }
        )

    write_result(result_path, "verify", verified)
    print(f"Verified {len(verified)} locally loaded plugins at their exact Git SHAs", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("acquire", "verify"))
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--installed-root", type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()

    specs = load_specs(args.manifest, args.config)
    if args.operation == "acquire":
        acquire(specs, args.source_root, args.result)
        return
    if args.installed_root is None:
        parser.error("verify requires --installed-root")
    verify(specs, args.source_root, args.installed_root, args.result)


if __name__ == "__main__":
    main()
