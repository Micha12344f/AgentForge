"""
Push changes to GitHub and create a GitHub Release with installer artifacts.

Prerequisites:
  - GitHub CLI (`gh`) authenticated: `gh auth login`
  - Git remote set to Micha12344f/Hedge-Edge-App
  - Installer already built (run build_installer.py first)

Usage:
    python create_release.py
    python create_release.py --project "C:\\path\\to\\Hedge-Edge-Front-end"
    python create_release.py --skip-push          # skip git operations
    python create_release.py --notes "Changelog"  # custom release notes
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


def get_version(project: Path) -> str:
    pkg = json.loads((project / "package.json").read_text(encoding="utf-8"))
    return pkg["version"]


def git_push(project: Path, version: str) -> None:
    git_root = project
    # Walk up to find .git directory
    while git_root != git_root.parent:
        if (git_root / ".git").exists():
            break
        git_root = git_root.parent
    else:
        print("ERROR: .git directory not found")
        sys.exit(1)

    print(f"\n=== Git push from {git_root} ===")
    run("git add -A", cwd=git_root)

    # Check if there are staged changes
    status = run("git diff --cached --quiet", cwd=git_root, check=False)
    if status.returncode != 0:
        run(f'git commit -m "release: v{version}"', cwd=git_root)
    else:
        print("No staged changes — skipping commit")

    # Push, handling rejected pushes
    push_result = run("git push origin main", cwd=git_root, check=False)
    if push_result.returncode != 0:
        print("Push rejected — pulling and retrying...")
        run("git pull --no-edit origin main", cwd=git_root)
        run("git push origin main", cwd=git_root)


def create_github_release(project: Path, version: str, notes: str) -> None:
    release_dir = project / "release"
    tag = f"v{version}"
    exe = release_dir / f"HedgeEdge-{version}-win-x64.exe"
    blockmap = release_dir / f"HedgeEdge-{version}-win-x64.exe.blockmap"
    latest_yml = release_dir / "latest.yml"

    # Validate artifacts exist
    missing = [f for f in [exe, blockmap, latest_yml] if not f.exists()]
    if missing:
        print("ERROR: Missing release artifacts:")
        for m in missing:
            print(f"  - {m.name}")
        print("Run build_installer.py first.")
        sys.exit(1)

    # Check if release already exists
    check = run(f"gh release view {tag} --repo {GITHUB_REPO}", cwd=project, check=False)
    if check.returncode == 0:
        print(f"Release {tag} already exists. Delete it first or bump the version.")
        sys.exit(1)

    print(f"\n=== Creating GitHub Release {tag} ===")
    cmd = (
        f'gh release create {tag}'
        f' "{exe}"'
        f' "{blockmap}"'
        f' "{latest_yml}"'
        f' --repo {GITHUB_REPO}'
        f' --title "{tag}"'
        f' --notes "{notes}"'
    )
    run(cmd, cwd=project)

    print(f"\nRelease {tag} created successfully!")
    print(f"https://github.com/{GITHUB_REPO}/releases/tag/{tag}")


def verify_release(project: Path) -> None:
    print("\n=== Verifying releases ===")
    run(f"gh release list --repo {GITHUB_REPO} --limit 5", cwd=project)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Hedge Edge GitHub Release")
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT, help="Project root")
    parser.add_argument("--skip-push", action="store_true", help="Skip git commit/push")
    parser.add_argument("--notes", default="", help="Custom release notes")
    args = parser.parse_args()

    project = args.project
    version = get_version(project)

    if not args.notes:
        args.notes = f"Release v{version}"

    print(f"Creating release for Hedge Edge v{version}")

    # Step 1: Git push
    if not args.skip_push:
        git_push(project, version)

    # Step 2: Create GitHub release
    create_github_release(project, version, args.notes)

    # Step 3: Verify
    verify_release(project)


if __name__ == "__main__":
    main()
