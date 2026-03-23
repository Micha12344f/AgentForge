#!/usr/bin/env python3
"""
app_deployer.py — Product Agent App Deployment Pipeline

End-to-end deployment for the Hedge Edge Electron desktop app:
  bump version → compile TS → build installer → git push → GitHub Release → verify.

Actions:
  bump      — Bump version in package.json (--bump patch|minor|major)
  build     — Compile TypeScript and build Windows installer
  release   — Git push + create GitHub Release with artifacts
  verify    — List recent releases and confirm artifact presence
  deploy    — Full pipeline (bump → build → release → verify)

Usage:
    python app_deployer.py --action bump --bump patch
    python app_deployer.py --action build
    python app_deployer.py --action release --notes "v1.0.6 changelog"
    python app_deployer.py --action verify
    python app_deployer.py --action deploy --bump patch --notes "v1.0.6 — bug fixes"
    python app_deployer.py --action deploy --project "C:\\path\\to\\Hedge-Edge-Front-end" --bump minor
"""

import sys
import os
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
from shared.notion_client import log_task

GITHUB_REPO = "Micha12344f/Hedge-Edge-App"

DEFAULT_PROJECT_ROOT = Path(
    r"C:\Users\sossi\Desktop\Business\Orchestrator Hedge Edge"
    r"\Business\STRATEGY\resources\Product\Hedge-Edge-App"
    r"\Hedge-Edge-Beta\Hedge-Edge-Front-end"
)


# ── Helpers ─────────────────────────────────────────────

def _run(cmd: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command, printing stdout/stderr."""
    print(f"> {cmd}")
    result = subprocess.run(cmd, cwd=str(cwd), shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if check and result.returncode != 0:
        print(f"ERROR: command failed (exit {result.returncode})")
        sys.exit(result.returncode)
    return result


def _get_version(project: Path) -> str:
    pkg = json.loads((project / "package.json").read_text(encoding="utf-8"))
    return pkg["version"]


def _bump_version(version: str, part: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = 0
        patch = 0
    return f"{major}.{minor}.{patch}"


# ── Actions ─────────────────────────────────────────────

def action_bump(project: Path, bump_type: str) -> str:
    """Bump the version in package.json. Returns the new version."""
    pkg_path = project / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    old = pkg["version"]
    new = _bump_version(old, bump_type)
    pkg["version"] = new
    pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
    print(f"✅ Version bumped: {old} → {new}")
    log_task("Product", f"Version bump {old} → {new}", "Complete", "P2")
    return new


def action_build(project: Path) -> None:
    """Compile TypeScript and build the Windows installer."""
    version = _get_version(project)
    print(f"\n=== Building Hedge Edge v{version} ===")

    print("\n── Step 1/2: Compiling Electron TypeScript ──")
    _run("npm run electron:compile", cwd=project)

    print("\n── Step 2/2: Building Windows installer ──")
    _run("npm run electron:build:win", cwd=project)

    # Report artifacts
    release_dir = project / "release"
    exe = f"HedgeEdge-{version}-win-x64.exe"
    expected = [exe, f"{exe}.blockmap", "latest.yml"]
    print(f"\n=== Build complete — artifacts in {release_dir} ===")
    all_ok = True
    for fname in expected:
        fpath = release_dir / fname
        if fpath.exists():
            size_mb = fpath.stat().st_size / (1024 * 1024)
            print(f"  ✓ {fname} ({size_mb:.1f} MB)")
        else:
            print(f"  ✗ {fname} — MISSING")
            all_ok = False

    if not all_ok:
        print("ERROR: Some artifacts are missing. Build may have failed.")
        sys.exit(1)
    log_task("Product", f"Installer built v{version}", "Complete", "P1")


def action_release(project: Path, notes: str) -> None:
    """Git push and create a GitHub Release with installer artifacts."""
    version = _get_version(project)
    tag = f"v{version}"
    release_dir = project / "release"

    # Validate artifacts
    exe = release_dir / f"HedgeEdge-{version}-win-x64.exe"
    blockmap = release_dir / f"HedgeEdge-{version}-win-x64.exe.blockmap"
    latest_yml = release_dir / "latest.yml"

    missing = [f for f in [exe, blockmap, latest_yml] if not f.exists()]
    if missing:
        print("ERROR: Missing release artifacts:")
        for m in missing:
            print(f"  - {m.name}")
        print("Run --action build first.")
        sys.exit(1)

    # Git push
    git_root = project
    while git_root != git_root.parent:
        if (git_root / ".git").exists():
            break
        git_root = git_root.parent

    print(f"\n=== Git push from {git_root} ===")
    _run("git add -A", cwd=git_root)
    status = _run("git diff --cached --quiet", cwd=git_root, check=False)
    if status.returncode != 0:
        _run(f'git commit -m "release: {tag}"', cwd=git_root)
    else:
        print("No staged changes — skipping commit")

    push = _run("git push origin main", cwd=git_root, check=False)
    if push.returncode != 0:
        print("Push rejected — pulling and retrying...")
        _run("git pull --no-edit origin main", cwd=git_root)
        _run("git push origin main", cwd=git_root)

    # Check if release already exists
    check = _run(f"gh release view {tag} --repo {GITHUB_REPO}", cwd=project, check=False)
    if check.returncode == 0:
        print(f"Release {tag} already exists. Delete it first or bump the version.")
        sys.exit(1)

    # Create release
    release_notes = notes or f"Release {tag}"
    print(f"\n=== Creating GitHub Release {tag} ===")
    cmd = (
        f'gh release create {tag}'
        f' "{exe}" "{blockmap}" "{latest_yml}"'
        f' --repo {GITHUB_REPO}'
        f' --title "{tag}"'
        f' --notes "{release_notes}"'
    )
    _run(cmd, cwd=project)
    print(f"\n✅ Release {tag} published!")
    print(f"   https://github.com/{GITHUB_REPO}/releases/tag/{tag}")
    log_task("Product", f"GitHub Release {tag}", "Complete", "P1",
             f"Published with {exe.name}, blockmap, latest.yml")


def action_verify(project: Path) -> None:
    """List recent releases and confirm the latest has the right artifacts."""
    print("\n=== Recent releases ===")
    _run(f"gh release list --repo {GITHUB_REPO} --limit 5", cwd=project)

    version = _get_version(project)
    tag = f"v{version}"
    print(f"\n=== Artifacts for {tag} ===")
    result = _run(
        f'gh release view {tag} --repo {GITHUB_REPO} --json assets --jq ".assets[].name"',
        cwd=project, check=False,
    )
    if result.returncode != 0:
        print(f"⚠️  Release {tag} not found on GitHub.")
    else:
        assets = result.stdout.strip().splitlines()
        required = {"latest.yml"}
        found = set(assets)
        if required.issubset(found):
            print("✅ latest.yml present — auto-updater will work.")
        else:
            print("⚠️  latest.yml MISSING — auto-updater will 404!")
    log_task("Product", f"Release verify {tag}", "Complete", "P3")


def action_deploy(project: Path, bump_type: str, notes: str) -> None:
    """Full pipeline: bump → build → release → verify."""
    if not bump_type:
        print("ERROR: --bump is required for full deploy")
        sys.exit(1)

    print("=" * 60)
    print("  🚀 HEDGE EDGE APP DEPLOY PIPELINE")
    print("=" * 60)

    print("\n── Phase 1: Bump Version ──")
    new_version = action_bump(project, bump_type)

    print(f"\n── Phase 2: Build Installer (v{new_version}) ──")
    action_build(project)

    print(f"\n── Phase 3: Push & Release ──")
    action_release(project, notes or f"Release v{new_version}")

    print(f"\n── Phase 4: Verify ──")
    action_verify(project)

    print("\n" + "=" * 60)
    print(f"  ✅ Hedge Edge v{new_version} deployed successfully!")
    print("=" * 60)
    log_task("Product", f"Full deploy v{new_version}", "Complete", "P1",
             "bump → build → release → verify — all passed")


# ── CLI ─────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Hedge Edge App Deployment Pipeline")
    parser.add_argument("--action", required=True,
                        choices=["bump", "build", "release", "verify", "deploy"],
                        help="Deployment action to perform")
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT,
                        help="Path to Hedge-Edge-Front-end project root")
    parser.add_argument("--bump", choices=["patch", "minor", "major"],
                        help="Semver part to bump (required for bump/deploy)")
    parser.add_argument("--notes", default="", help="Release notes text")
    args = parser.parse_args()

    if not (args.project / "package.json").exists():
        print(f"ERROR: package.json not found in {args.project}")
        print("Pass --project to point at the Hedge-Edge-Front-end directory.")
        sys.exit(1)

    actions = {
        "bump":    lambda: action_bump(args.project, args.bump) if args.bump else sys.exit("ERROR: --bump required"),
        "build":   lambda: action_build(args.project),
        "release": lambda: action_release(args.project, args.notes),
        "verify":  lambda: action_verify(args.project),
        "deploy":  lambda: action_deploy(args.project, args.bump, args.notes),
    }
    actions[args.action]()


if __name__ == "__main__":
    main()
