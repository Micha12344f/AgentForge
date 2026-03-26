from __future__ import annotations

import inspect
from pathlib import Path

from dotenv import load_dotenv


def find_workspace_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__).resolve()).parent
    for candidate in [current, *current.parents]:
        if (candidate / "Business").is_dir() and (candidate / "shared").is_dir():
            return candidate
    # Fallback for Docker/CI environments where workspace structure doesn't exist.
    # Railway injects env vars directly — .env files aren't needed there.
    return (start or Path(__file__).resolve()).parent.parent


def infer_department(source_path: Path, workspace_root: Path) -> str | None:
    try:
        relative = source_path.resolve().relative_to(workspace_root)
    except ValueError:
        return None

    parts = relative.parts
    if len(parts) >= 2 and parts[0] == "Business":
        return parts[1]
    return None


def infer_subdepartment(source_path: Path, workspace_root: Path) -> str | None:
    try:
        relative = source_path.resolve().relative_to(workspace_root)
    except ValueError:
        return None

    parts = relative.parts
    if len(parts) >= 4 and parts[0] == "Business" and parts[2] in {"directives", "executions", "resources"}:
        return parts[3]
    return None


def _infer_source_from_stack(workspace_root: Path) -> Path | None:
    loader_file = Path(__file__).resolve()
    for frame in inspect.stack()[1:]:
        frame_path = Path(frame.filename).resolve()
        if frame_path == loader_file:
            continue
        try:
            frame_path.relative_to(workspace_root)
        except ValueError:
            continue
        return frame_path
    return None


def load_env_for_source(
    source_file: str | Path | None = None,
    department: str | None = None,
    *,
    include_root_fallback: bool = True,
) -> dict[str, object]:
    source_path = Path(source_file).resolve() if source_file else Path(__file__).resolve()
    workspace_root = find_workspace_root(source_path)

    inferred_source = Path(source_file).resolve() if source_file else _infer_source_from_stack(workspace_root)
    inferred_department = department
    inferred_subdepartment = None
    if inferred_department is None and inferred_source is not None:
        inferred_department = infer_department(inferred_source, workspace_root)
    if inferred_source is not None:
        inferred_subdepartment = infer_subdepartment(inferred_source, workspace_root)

    loaded_files: list[str] = []

    root_env = workspace_root / ".env"
    if include_root_fallback and root_env.is_file():
        load_dotenv(root_env, override=False)
        loaded_files.append(str(root_env))

    if inferred_department:
        department_env = workspace_root / "Business" / inferred_department / "resources" / ".env"
        if department_env.is_file():
            load_dotenv(department_env, override=True)
            loaded_files.append(str(department_env))

        if inferred_subdepartment:
            subdepartment_env = workspace_root / "Business" / inferred_department / "resources" / inferred_subdepartment / ".env"
            if subdepartment_env.is_file():
                load_dotenv(subdepartment_env, override=True)
                loaded_files.append(str(subdepartment_env))

    return {
        "workspace_root": str(workspace_root),
        "department": inferred_department,
        "subdepartment": inferred_subdepartment,
        "loaded_files": loaded_files,
    }


def load_department_env(source_file: str | Path, department: str) -> dict[str, object]:
    return load_env_for_source(source_file=source_file, department=department)