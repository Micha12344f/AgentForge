"""
Bump the version in package.json for the Hedge Edge Electron app.

Usage:
    python bump_version.py --bump patch       # 1.0.4 → 1.0.5
    python bump_version.py --bump minor       # 1.0.4 → 1.1.0
    python bump_version.py --bump major       # 1.0.4 → 2.0.0
    python bump_version.py --set 1.2.3        # set explicit version
"""

import argparse
import json
import sys
from pathlib import Path

# Default project root (adjust if running from a different location)
DEFAULT_PROJECT_ROOT = Path(
    r"C:\Users\sossi\Desktop\Business\Orchestrator Hedge Edge"
    r"\Orchestrator\Hedge Edge Business\IDE 1\Context\Hedge Edge App"
    r"\Hedge-Edge-Beta\Hedge-Edge-Front-end"
)


def read_package_json(project_root: Path) -> dict:
    pkg_path = project_root / "package.json"
    if not pkg_path.exists():
        print(f"ERROR: {pkg_path} not found")
        sys.exit(1)
    return json.loads(pkg_path.read_text(encoding="utf-8"))


def write_package_json(project_root: Path, data: dict) -> None:
    pkg_path = project_root / "package.json"
    pkg_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def bump(version_str: str, part: str) -> str:
    parts = list(map(int, version_str.split(".")))
    if len(parts) != 3:
        print(f"ERROR: unexpected version format '{version_str}'")
        sys.exit(1)

    major, minor, patch = parts
    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        print(f"ERROR: unknown bump type '{part}'")
        sys.exit(1)

    return f"{major}.{minor}.{patch}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump Hedge Edge app version")
    parser.add_argument("--bump", choices=["patch", "minor", "major"], help="Semver part to bump")
    parser.add_argument("--set", dest="explicit", help="Set an explicit version string (e.g. 2.0.0)")
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT_ROOT, help="Path to project root")
    args = parser.parse_args()

    if not args.bump and not args.explicit:
        parser.error("Provide --bump (patch|minor|major) or --set <version>")

    pkg = read_package_json(args.project)
    old_version = pkg["version"]

    if args.explicit:
        new_version = args.explicit
    else:
        new_version = bump(old_version, args.bump)

    pkg["version"] = new_version
    write_package_json(args.project, pkg)

    print(f"Version bumped: {old_version} → {new_version}")
    print(f"Updated: {args.project / 'package.json'}")


if __name__ == "__main__":
    main()
