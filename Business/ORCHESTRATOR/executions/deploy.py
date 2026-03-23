"""
Full Hedge Edge deployment pipeline — runs all steps end-to-end.

Steps:
  1. Bump version in package.json
  2. Compile Electron TypeScript
  3. Build Windows installer
  4. Commit and push to GitHub
  5. Create GitHub Release with artifacts
  6. Verify release

Usage:
    python deploy.py --bump patch
    python deploy.py --bump minor
    python deploy.py --bump major
    python deploy.py --set 2.0.0
    python deploy.py --bump patch --notes "Fixed login bug"
    python deploy.py --bump patch --dry-run   # preview without executing
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_PROJECT_ROOT = Path(
    r"C:\Users\sossi\Desktop\Business\Orchestrator Hedge Edge"
    r"\Orchestrator\Hedge Edge Business\IDE 1\Context\Hedge Edge App"
    r"\Hedge-Edge-Beta\Hedge-Edge-Front-end"
)

GITHUB_REPO = "Micha12344f/Hedge-Edge-App"


def run(cmd: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  > {cmd}")
    result = subprocess.run(cmd, cwd=str(cwd), shell=True, capture_output=True, text=True)
    if result.stdout:
        for line in result.stdout.strip().splitlines()[:20]:
            print(f"    {line}")
    if result.stderr:
        for line in result.stderr.strip().splitlines()[:10]:
            print(f"    {line}")
    if check and result.returncode != 0:
        print(f"  ERROR: exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def get_version(project: Path) -> str:
    pkg = json.loads((project / "package.json").read_text(encoding="utf-8"))
    return pkg["version"]


def set_version(project: Path, version: str) -> None:
    pkg_path = project / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    pkg["version"] = version
    pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")


def bump_version(current: str, part: str) -> str:
    major, minor, patch = map(int, current.split("."))
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


def find_git_root(project: Path) -> Path:
    p = project
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("ERROR: .git not found")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy Hedge Edge app update")
    parser.add_argument("--bump", choices=["patch", "minor", "major"], help="Version bump type")
    parser.add_argument("--set", dest="explicit", help="Explicit version")
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT, help="Project root")
    parser.add_argument("--notes", default="", help="Release notes")
    parser.add_argument("--dry-run", action="store_true", help="Preview without executing")
    args = parser.parse_args()

    project = args.project
    if not (project / "package.json").exists():
        print(f"ERROR: package.json not found in {project}")
        sys.exit(1)

    old_version = get_version(project)

    if args.explicit:
        new_version = args.explicit
    elif args.bump:
        new_version = bump_version(old_version, args.bump)
    else:
        parser.error("Provide --bump or --set")
        return

    release_notes = args.notes or f"Release v{new_version}"
    git_root = find_git_root(project)

    print("=" * 60)
    print(f"  Hedge Edge Deploy Pipeline")
    print(f"  Version:  {old_version} → {new_version}")
    print(f"  Project:  {project}")
    print(f"  Git root: {git_root}")
    print(f"  Repo:     {GITHUB_REPO}")
    print(f"  Notes:    {release_notes}")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN] Would execute:")
        print(f"  1. Bump version to {new_version}")
        print(f"  2. npm run electron:compile")
        print(f"  3. npm run electron:build:win")
        print(f"  4. git commit + push")
        print(f"  5. gh release create v{new_version}")
        return

    # --- Step 1: Bump version ---
    print(f"\n[1/5] Bumping version: {old_version} → {new_version}")
    set_version(project, new_version)
    print(f"  Updated package.json")

    # --- Step 2: Compile TypeScript ---
    print(f"\n[2/5] Compiling Electron TypeScript...")
    run("npm run electron:compile", cwd=project)

    # --- Step 3: Build installer ---
    print(f"\n[3/5] Building Windows installer...")
    run("npm run electron:build:win", cwd=project)

    # Verify artifacts
    release_dir = project / "release"
    exe = release_dir / f"HedgeEdge-{new_version}-win-x64.exe"
    blockmap = release_dir / f"HedgeEdge-{new_version}-win-x64.exe.blockmap"
    latest_yml = release_dir / "latest.yml"

    for artifact in [exe, blockmap, latest_yml]:
        if not artifact.exists():
            print(f"  ERROR: Missing {artifact.name}")
            sys.exit(1)
        size_mb = artifact.stat().st_size / (1024 * 1024)
        print(f"  ✓ {artifact.name} ({size_mb:.1f} MB)")

    # --- Step 4: Git commit & push ---
    print(f"\n[4/5] Committing and pushing...")
    run("git add -A", cwd=git_root)
    status = run("git diff --cached --quiet", cwd=git_root, check=False)
    if status.returncode != 0:
        run(f'git commit -m "release: v{new_version}"', cwd=git_root)

    push_result = run("git push origin main", cwd=git_root, check=False)
    if push_result.returncode != 0:
        print("  Push rejected — pulling and retrying...")
        run("git pull --no-edit origin main", cwd=git_root)
        run("git push origin main", cwd=git_root)

    # --- Step 5: Create GitHub Release ---
    print(f"\n[5/5] Creating GitHub Release v{new_version}...")
    tag = f"v{new_version}"

    # Check for existing release
    check = run(f"gh release view {tag} --repo {GITHUB_REPO}", cwd=project, check=False)
    if check.returncode == 0:
        print(f"  Release {tag} already exists — skipping creation")
    else:
        cmd = (
            f'gh release create {tag}'
            f' "{exe}"'
            f' "{blockmap}"'
            f' "{latest_yml}"'
            f' --repo {GITHUB_REPO}'
            f' --title "{tag}"'
            f' --notes "{release_notes}"'
        )
        run(cmd, cwd=project)

    # --- Done ---
    print("\n" + "=" * 60)
    print(f"  Deploy complete: v{new_version}")
    print(f"  https://github.com/{GITHUB_REPO}/releases/tag/{tag}")
    print("=" * 60)

    # Quick verification
    run(f"gh release list --repo {GITHUB_REPO} --limit 3", cwd=project)


if __name__ == "__main__":
    main()
