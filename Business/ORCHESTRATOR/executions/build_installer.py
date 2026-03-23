"""
Build the Hedge Edge Electron Windows installer.

Steps:
  1. Compile Electron TypeScript (electron:compile)
  2. Build Vite frontend + package with electron-builder (electron:build:win)
  3. Report output artifacts in release/

Usage:
    python build_installer.py
    python build_installer.py --project "C:\\path\\to\\Hedge-Edge-Front-end"
"""

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_PROJECT_ROOT = Path(
    r"C:\Users\sossi\Desktop\Business\Orchestrator Hedge Edge"
    r"\Orchestrator\Hedge Edge Business\IDE 1\Context\Hedge Edge App"
    r"\Hedge-Edge-Beta\Hedge-Edge-Front-end"
)


def run(cmd: str, cwd: Path) -> None:
    print(f"\n> {cmd}")
    result = subprocess.run(cmd, cwd=str(cwd), shell=True)
    if result.returncode != 0:
        print(f"ERROR: command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def get_version(project: Path) -> str:
    import json
    pkg = json.loads((project / "package.json").read_text(encoding="utf-8"))
    return pkg["version"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Hedge Edge Windows installer")
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT, help="Project root")
    parser.add_argument("--skip-compile", action="store_true", help="Skip TypeScript compilation")
    args = parser.parse_args()

    project = args.project
    if not (project / "package.json").exists():
        print(f"ERROR: package.json not found in {project}")
        sys.exit(1)

    version = get_version(project)
    print(f"Building Hedge Edge v{version} Windows installer...")

    # Step 1: Compile TypeScript
    if not args.skip_compile:
        print("\n=== Step 1/2: Compiling Electron TypeScript ===")
        run("npm run electron:compile", cwd=project)

    # Step 2: Build installer
    print("\n=== Step 2/2: Building Windows installer ===")
    run("npm run electron:build:win", cwd=project)

    # Report artifacts
    release_dir = project / "release"
    print(f"\n=== Build complete ===")
    print(f"Artifacts in: {release_dir}")

    exe_name = f"HedgeEdge-{version}-win-x64.exe"
    expected_files = [exe_name, f"{exe_name}.blockmap", "latest.yml"]

    for fname in expected_files:
        fpath = release_dir / fname
        if fpath.exists():
            size_mb = fpath.stat().st_size / (1024 * 1024)
            print(f"  ✓ {fname} ({size_mb:.1f} MB)")
        else:
            print(f"  ✗ {fname} — MISSING")


if __name__ == "__main__":
    main()
