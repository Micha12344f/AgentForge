# Skill Builder Templates — DOE Scaffolding Reference

> **Skill**: Skill Builder
> **Department**: ORCHESTRATOR
> **Directive**: `Business/ORCHESTRATOR/directives/skill-builder.md`
> **Execution**: `Business/ORCHESTRATOR/executions/skill_builder.py`

These are the canonical templates used when scaffolding new skills. The execution script (`skill_builder.py`) uses these patterns programmatically. Agents can also reference these templates directly when creating skills manually.

---

## Template 1 — Directive File

**Path pattern**: `Business/<DEPARTMENT>/directives/<skill-slug>.md`

```markdown
# <Skill Display Name> — <DEPARTMENT> Directive

## Purpose

<One paragraph describing what this skill does and why it exists.>

## Owner

<DEPARTMENT>

## Trigger

<When to use this skill — the conditions or requests that activate it.>

## Execution Script

| Layer | Path |
|-------|------|
| Execution | `Business/<DEPARTMENT>/executions/<skill_slug>.py` |

<Brief description of what the execution script does.>

## Resources

| Resource | Path | Description |
|----------|------|-------------|
| <Resource Name> | `Business/<DEPARTMENT>/resources/<filename>` | <What it contains> |

## How It Works — Step by Step

### Step 1 — <Step Title>

<What happens in this step.>

### Step 2 — <Step Title>

<What happens in this step.>

<!-- Add more steps as needed -->
```

---

## Template 2 — Execution Stub (Python)

**Path pattern**: `Business/<DEPARTMENT>/executions/<skill_slug>.py`

```python
"""
<Skill Display Name> — <DEPARTMENT> Execution Script

Directive: Business/<DEPARTMENT>/directives/<skill-slug>.md
Resource:  Business/<DEPARTMENT>/resources/<resource-filename>

<Description of what this script does.>
"""

from __future__ import annotations


def main() -> None:
    """Entry point for <Skill Display Name>."""
    # TODO: Implement the skill logic
    raise NotImplementedError("<Skill Display Name> execution not yet implemented")


if __name__ == "__main__":
    main()
```

---

## Template 3 — Resource File

**Path pattern**: `Business/<DEPARTMENT>/resources/<resource-name>.md`

```markdown
# <Resource Name> — Resource for <Skill Display Name>

> **Skill**: <Skill Display Name>
> **Department**: <DEPARTMENT>
> **Directive**: `Business/<DEPARTMENT>/directives/<skill-slug>.md`

## Description

<What this resource contains and how to use it.>

---

<!-- Add fixed reference content below -->
```

---

## Template 4 — SKILL.md Entry

**Append to**: `Business/<DEPARTMENT>/SKILL.md`

```markdown
### Skill N — <Skill Display Name>
| Layer | Path |
|-------|------|
| Directive | `directives/<skill-slug>.md` |
| Executions | `executions/<skill_slug>.py` |
| Resources | `resources/<resource-name>.md` |
| Use for | <One-line description of when to use this skill> |
```

> **Note**: Replace `N` with the next sequential skill number in that department's SKILL.md.

---

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Skill slug | lowercase-kebab | `email-sender` |
| Directive filename | `<slug>.md` | `email-sender.md` |
| Execution filename | `<slug_underscored>.py` | `email_sender.py` |
| Resource filename | `<descriptive-name>.md` | `email-templates.md` |
| Display name | Title Case | `Email Sender` |

## Department Paths

| Department | Root |
|------------|------|
| ENGINEERING | `Business/engineering/` |
| PRODUCT | `Business/PRODUCT/` |
| DELIVERY | `Business/DELIVERY/` |
| CONTENT | `Business/CONTENT/` |
| ORCHESTRATOR | `Business/ORCHESTRATOR/` |
