# Skill Builder Directive

## Purpose

Create new skills for **any** agent department in the AgentForge workspace — including the Orchestrator itself. This is the meta-skill: it produces DOE-compliant skill packs (directive + execution + resources) and registers them in the target department's `SKILL.md`.

## Owner

ORCHESTRATOR — only the Orchestrator may create cross-department skills or restructure DOE layout (see `Business/agents.md` governance model).

## Trigger

Use this skill when:
- A new capability is needed for any department agent
- An existing department needs a new automated workflow
- The Orchestrator itself needs a new skill

## Execution Script

| Layer | Path |
|-------|------|
| Execution | `Business/ORCHESTRATOR/executions/skill_builder.py` |

The Python script scaffolds the full DOE skill pack for a target department. It creates the directive markdown, execution stub, and optional resource files, then appends the skill entry to the target department's `SKILL.md`.

## Resource Templates

| Resource | Path |
|----------|------|
| DOE Templates | `Business/ORCHESTRATOR/resources/skill-builder-templates.md` |

Contains the canonical templates for directive files, execution stubs, and resource files that the skill builder uses as scaffolding.

---

## How It Works — Step by Step

### Step 1 — Gather Skill Requirements

Before creating anything, collect the following (use `vscode/askQuestions` if interactive):

| # | Question | Required |
|---|----------|----------|
| 1 | **Skill name** (slug, e.g. `email-sender`) | Yes |
| 2 | **Target department** (`ENGINEERING`, `PRODUCT`, `DELIVERY`, `CONTENT`, `ORCHESTRATOR`) | Yes |
| 3 | **Skill description** — one paragraph explaining what the skill does | Yes |
| 4 | **Execution needed?** — does this skill require a Python script? | Yes |
| 5 | **Execution description** — what the Python script does (if applicable) | If exec = yes |
| 6 | **Resources needed?** — list of fixed reference files (frameworks, tool docs, config templates) | Optional |
| 7 | **Resource descriptions** — what each resource contains | If resources listed |

### Step 2 — Validate Target Department

Confirm the target department exists under `Business/`. Valid departments:
- `ENGINEERING`
- `PRODUCT`
- `DELIVERY`
- `CONTENT`
- `ORCHESTRATOR`

Directory note:
- The department identifier stays `ENGINEERING`, but its folder path is `Business/engineering/`.
- The other department folders currently remain uppercase.

### Step 3 — Create the Directive File

Create `Business/<DEPARTMENT>/directives/<skill-slug>.md` following the directive template in `Business/ORCHESTRATOR/resources/skill-builder-templates.md`.

The directive **must** contain:
- Skill name and purpose
- Owner department
- Trigger conditions (when to use this skill)
- **Execution script path** — absolute workspace-relative path to the Python file in `executions/`
- **Resource paths** — absolute workspace-relative paths to each resource file in `resources/`
- Step-by-step instructions for how the skill operates
- What each execution script does
- What each resource file contains and how to use it

### Step 4 — Create the Execution Script

If the skill requires a Python script, create `Business/<DEPARTMENT>/executions/<skill_slug>.py`.

The script should:
- Have a clear module docstring explaining its purpose
- Reference the directive path in a comment at the top
- Be runnable standalone or importable by an agent
- Follow existing execution patterns (see `Business/engineering/executions/agent_builder.py` for reference)

### Step 5 — Create Resource Files

For each resource needed, create `Business/<DEPARTMENT>/resources/<resource-name>.md` (or other appropriate format).

Resources are **fixed reference material** — things that don't change frequently:
- Tool/framework documentation summaries
- Configuration templates
- Checklists and runbooks
- Schema definitions
- Fixed API patterns (not live API docs that change)

### Step 6 — Update the Department SKILL.md (Last Step)

**This is always the last step.** Append a new skill entry to the target department's `SKILL.md` following the existing format:

```markdown
### Skill N — <Skill Display Name>
| Layer | Path |
|-------|------|
| Directive | `directives/<skill-slug>.md` |
| Executions | `executions/<skill_slug>.py` |
| Resources | `resources/<resource-name>.md` |
| Use for | <one-line description of when to use this skill> |
```

Increment the skill number based on the last skill in the file.

---

## Validation Checklist

After creating a skill, verify:

- [ ] Directive file exists at `Business/<DEPT>/directives/<skill-slug>.md`
- [ ] Directive contains execution path(s) and resource path(s)
- [ ] Directive describes the skill purpose, trigger, and step-by-step workflow
- [ ] Execution script exists at `Business/<DEPT>/executions/<skill_slug>.py` (if needed)
- [ ] Execution script has a docstring and is syntactically valid
- [ ] Resource files exist at their documented paths (if any)
- [ ] Target department `SKILL.md` has been updated with the new skill entry
- [ ] Skill number in SKILL.md is correctly incremented
- [ ] All file paths in the directive match the actual file locations

## Anti-Patterns

- **Never create a skill without a directive** — the directive is the entry point; without it, the skill is invisible
- **Never skip the SKILL.md update** — unregistered skills cannot be discovered by agents
- **Never put volatile content in resources** — resources are fixed reference material, not live API docs
- **Never create executions without documenting them in the directive** — every Python script must have its path listed in the directive
- **Never update SKILL.md before all files are created** — SKILL.md is always the last step to avoid referencing nonexistent files
