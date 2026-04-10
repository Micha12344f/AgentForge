"""
Skill Builder — Orchestrator Execution Script

Directive: Business/ORCHESTRATOR/directives/skill-builder.md
Templates: Business/ORCHESTRATOR/resources/skill-builder-templates.md

Scaffolds a complete DOE-compliant skill pack for any AgentForge department:
  1. Directive markdown  (directives/<skill-slug>.md)
  2. Execution stub       (executions/<skill_slug>.py)  — optional
  3. Resource files        (resources/<name>.md)          — optional
  4. SKILL.md registration (appends new skill entry)

Can be run standalone or imported by an agent.
"""

from __future__ import annotations

import os
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BUSINESS_ROOT = Path(__file__).resolve().parent.parent.parent  # Business/
VALID_DEPARTMENTS = {"ENGINEERING", "PRODUCT", "DELIVERY", "CONTENT", "ORCHESTRATOR"}
DEPARTMENT_DIR_NAMES = {
    "ENGINEERING": "engineering",
    "PRODUCT": "PRODUCT",
    "DELIVERY": "DELIVERY",
    "CONTENT": "CONTENT",
    "ORCHESTRATOR": "ORCHESTRATOR",
}

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ResourceSpec:
    """A single fixed resource file to create."""
    name: str          # e.g. "email-templates"
    filename: str      # e.g. "email-templates.md"
    description: str   # What this resource contains


@dataclass
class SkillSpec:
    """Everything needed to scaffold a new skill."""
    name: str                          # slug, e.g. "email-sender"
    department: str                    # e.g. "ENGINEERING"
    display_name: str                  # e.g. "Email Sender"
    description: str                   # One-paragraph purpose
    trigger: str                       # When to use this skill
    has_execution: bool = True
    execution_description: str = ""    # What the Python script does
    resources: list[ResourceSpec] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)  # Step-by-step instructions

    @property
    def slug(self) -> str:
        return self.name.lower().strip()

    @property
    def py_slug(self) -> str:
        return self.slug.replace("-", "_")

    @property
    def dept_root(self) -> Path:
        return BUSINESS_ROOT / self.dept_dir_name

    @property
    def dept_dir_name(self) -> str:
        return DEPARTMENT_DIR_NAMES[self.department]

    @property
    def directive_path(self) -> Path:
        return self.dept_root / "directives" / f"{self.slug}.md"

    @property
    def execution_path(self) -> Path:
        return self.dept_root / "executions" / f"{self.py_slug}.py"

    @property
    def resource_paths(self) -> list[Path]:
        return [self.dept_root / "resources" / r.filename for r in self.resources]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_spec(spec: SkillSpec) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errors: list[str] = []

    if not spec.name or not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", spec.slug):
        errors.append(f"Invalid skill slug: '{spec.name}'. Must be lowercase-kebab (e.g. email-sender).")

    if spec.department not in VALID_DEPARTMENTS:
        errors.append(f"Unknown department: '{spec.department}'. Valid: {', '.join(sorted(VALID_DEPARTMENTS))}")

    if not spec.display_name.strip():
        errors.append("display_name is required.")

    if not spec.description.strip():
        errors.append("description is required.")

    dept_root = BUSINESS_ROOT / DEPARTMENT_DIR_NAMES[spec.department]
    if not dept_root.is_dir():
        errors.append(f"Department folder does not exist: {dept_root}")

    return errors


# ---------------------------------------------------------------------------
# Directive generator
# ---------------------------------------------------------------------------


def _build_directive(spec: SkillSpec) -> str:
    """Generate the directive markdown content."""
    lines: list[str] = []

    # Header
    lines.append(f"# {spec.display_name} — {spec.department} Directive\n")
    lines.append(f"## Purpose\n\n{spec.description}\n")
    lines.append(f"## Owner\n\n{spec.department}\n")
    lines.append(f"## Trigger\n\n{spec.trigger}\n")

    # Execution path table
    if spec.has_execution:
        lines.append("## Execution Script\n")
        lines.append("| Layer | Path |")
        lines.append("|-------|------|")
        lines.append(f"| Execution | `Business/{spec.dept_dir_name}/executions/{spec.py_slug}.py` |\n")
        if spec.execution_description:
            lines.append(f"{spec.execution_description}\n")

    # Resource paths table
    if spec.resources:
        lines.append("## Resources\n")
        lines.append("| Resource | Path | Description |")
        lines.append("|----------|------|-------------|")
        for r in spec.resources:
            lines.append(
                f"| {r.name} | `Business/{spec.dept_dir_name}/resources/{r.filename}` | {r.description} |"
            )
        lines.append("")

    # Step-by-step
    if spec.steps:
        lines.append("## How It Works — Step by Step\n")
        for i, step in enumerate(spec.steps, 1):
            lines.append(f"### Step {i}\n\n{step}\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Execution stub generator
# ---------------------------------------------------------------------------


def _build_execution_stub(spec: SkillSpec) -> str:
    """Generate a Python execution stub."""
    header = textwrap.dedent(f'''\
        """
        {spec.display_name} — {spec.department} Execution Script

        Directive: Business/{spec.dept_dir_name}/directives/{spec.slug}.md
        ''')

    if spec.resources:
        for r in spec.resources:
            header += f"Resource:  Business/{spec.dept_dir_name}/resources/{r.filename}\n"

    header += textwrap.dedent(f'''\

        {spec.execution_description or "TODO: Describe what this script does."}
        """

        from __future__ import annotations


        def main() -> None:
            """Entry point for {spec.display_name}."""
            # TODO: Implement the skill logic
            raise NotImplementedError("{spec.display_name} execution not yet implemented")


        if __name__ == "__main__":
            main()
    ''')

    return header


# ---------------------------------------------------------------------------
# Resource generator
# ---------------------------------------------------------------------------


def _build_resource(spec: SkillSpec, resource: ResourceSpec) -> str:
    """Generate a resource markdown file."""
    return textwrap.dedent(f"""\
        # {resource.name} — Resource for {spec.display_name}

        > **Skill**: {spec.display_name}
        > **Department**: {spec.department}
        > **Directive**: `Business/{spec.dept_dir_name}/directives/{spec.slug}.md`

        ## Description

        {resource.description}

        ---

        <!-- Add fixed reference content below -->
    """)


# ---------------------------------------------------------------------------
# SKILL.md updater
# ---------------------------------------------------------------------------


def _next_skill_number(skill_md_path: Path) -> int:
    """Parse SKILL.md and return the next skill number."""
    if not skill_md_path.exists():
        return 1
    content = skill_md_path.read_text(encoding="utf-8")
    matches = re.findall(r"###\s+Skill\s+(\d+)", content)
    if not matches:
        return 1
    return max(int(m) for m in matches) + 1


def _build_skill_entry(spec: SkillSpec, skill_number: int) -> str:
    """Build the SKILL.md entry block for the new skill."""
    lines: list[str] = []
    lines.append(f"### Skill {skill_number} — {spec.display_name}")
    lines.append("| Layer | Path |")
    lines.append("|-------|------|")
    lines.append(f"| Directive | `directives/{spec.slug}.md` |")
    if spec.has_execution:
        lines.append(f"| Executions | `executions/{spec.py_slug}.py` |")
    for r in spec.resources:
        lines.append(f"| Resources | `resources/{r.filename}` |")
    lines.append(f"| Use for | {spec.trigger} |")
    lines.append("")
    return "\n".join(lines)


def _append_to_skill_md(spec: SkillSpec) -> str:
    """Append a skill entry to the department's SKILL.md. Returns the entry text."""
    skill_md = spec.dept_root / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md}")

    skill_number = _next_skill_number(skill_md)
    entry = _build_skill_entry(spec, skill_number)

    with open(skill_md, "a", encoding="utf-8") as f:
        f.write("\n" + entry)

    return entry


# ---------------------------------------------------------------------------
# Orchestration — create all files
# ---------------------------------------------------------------------------


def create_skill(spec: SkillSpec, dry_run: bool = False) -> dict[str, str]:
    """
    Scaffold a complete DOE skill pack.

    Args:
        spec: The skill specification.
        dry_run: If True, return generated content without writing files.

    Returns:
        Dict mapping file paths (str) to their content.
    """
    errors = validate_spec(spec)
    if errors:
        raise ValueError("Skill spec validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    outputs: dict[str, str] = {}

    # 1. Directive
    directive_content = _build_directive(spec)
    outputs[str(spec.directive_path)] = directive_content

    # 2. Execution (optional)
    if spec.has_execution:
        exec_content = _build_execution_stub(spec)
        outputs[str(spec.execution_path)] = exec_content

    # 3. Resources
    for resource in spec.resources:
        res_path = spec.dept_root / "resources" / resource.filename
        res_content = _build_resource(spec, resource)
        outputs[str(res_path)] = res_content

    if dry_run:
        return outputs

    # Write files
    for path_str, content in outputs.items():
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError(f"File already exists: {path}. Remove it first or choose a different name.")
        path.write_text(content, encoding="utf-8")

    # 4. Update SKILL.md (always last)
    entry = _append_to_skill_md(spec)
    skill_md_path = spec.dept_root / "SKILL.md"
    outputs[str(skill_md_path) + " (appended)"] = entry

    return outputs


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------


def _prompt(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{question}{suffix}: ").strip()
    return answer or default


def _prompt_yes_no(question: str, default: bool = True) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    answer = input(f"{question}{suffix}: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def cli() -> None:
    """Interactive CLI for creating a new skill."""
    print("=" * 60)
    print("  AgentForge Skill Builder")
    print("=" * 60)
    print()

    name = _prompt("Skill slug (lowercase-kebab, e.g. email-sender)")
    display_name = _prompt("Display name (e.g. Email Sender)")
    department = _prompt("Target department", "ORCHESTRATOR").upper()
    description = _prompt("Skill description (one paragraph)")
    trigger = _prompt("When to use this skill (one line)")

    has_execution = _prompt_yes_no("Does this skill need a Python execution script?")
    execution_description = ""
    if has_execution:
        execution_description = _prompt("What does the execution script do?")

    resources: list[ResourceSpec] = []
    while _prompt_yes_no("Add a resource file?", default=not resources):
        r_name = _prompt("  Resource name (e.g. Email Templates)")
        r_filename = _prompt("  Resource filename (e.g. email-templates.md)")
        r_desc = _prompt("  Resource description")
        resources.append(ResourceSpec(name=r_name, filename=r_filename, description=r_desc))

    steps: list[str] = []
    print("\nEnter step-by-step instructions (empty line to stop):")
    step_num = 1
    while True:
        step = _prompt(f"  Step {step_num}")
        if not step:
            break
        steps.append(step)
        step_num += 1

    spec = SkillSpec(
        name=name,
        department=department,
        display_name=display_name,
        description=description,
        trigger=trigger,
        has_execution=has_execution,
        execution_description=execution_description,
        resources=resources,
        steps=steps,
    )

    errors = validate_spec(spec)
    if errors:
        print("\nValidation errors:")
        for e in errors:
            print(f"  ✗ {e}")
        return

    print(f"\nWill create skill '{display_name}' in {department}:")
    print(f"  Directive:  Business/{spec.dept_dir_name}/directives/{spec.slug}.md")
    if has_execution:
        print(f"  Execution:  Business/{spec.dept_dir_name}/executions/{spec.py_slug}.py")
    for r in resources:
        print(f"  Resource:   Business/{spec.dept_dir_name}/resources/{r.filename}")
    print(f"  SKILL.md:   Business/{spec.dept_dir_name}/SKILL.md (append entry)")

    if not _prompt_yes_no("\nProceed?"):
        print("Aborted.")
        return

    outputs = create_skill(spec)
    print(f"\nCreated {len(outputs)} files:")
    for path in outputs:
        print(f"  ✓ {path}")
    print("\nDone.")


if __name__ == "__main__":
    cli()
