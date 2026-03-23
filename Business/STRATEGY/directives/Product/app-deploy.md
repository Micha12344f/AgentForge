---
name: app-deploy
description: |
  End-to-end deployment pipeline for the Hedge Edge Electron desktop app.
  Covers version bumping, TypeScript compilation, Windows installer build,
  GitHub Release creation with auto-updater artifacts, and post-deploy verification.
---

# App Deployment

## Objective

Ship verified Hedge Edge app updates through a reproducible pipeline:
bump version → compile → build installer → push → create GitHub Release → verify.

## When to Use

- Ship a new version of the Hedge Edge Electron app
- Build a Windows installer (.exe) for distribution
- Create a GitHub Release with auto-updater artifacts
- Bump the app version (patch / minor / major)
- Hotfix deployment outside normal release cadence

## Repository & Build Context

| Key | Value |
|-----|-------|
| GitHub repo | `Micha12344f/Hedge-Edge-App` |
| Workspace app clone | `Business/STRATEGY/resources/Product/Hedge-Edge-App` |
| Frontend root | `Business/STRATEGY/resources/Product/Hedge-Edge-App/Hedge-Edge-Beta/Hedge-Edge-Front-end` |
| Electron entry | `electron/main.ts` → compiled to `dist-electron/main.js` |
| Build tool | `electron-builder` (v26.4.0) |
| Auto-updater | `electron-updater` via GitHub Releases provider |
| Installer output | `release/HedgeEdge-<version>-win-x64.exe` |
| Required artifacts | `.exe`, `.exe.blockmap`, `latest.yml` |

## Deployment Steps

All build and release commands below target the in-workspace app clone at:
`Business/STRATEGY/resources/Product/Hedge-Edge-App/Hedge-Edge-Beta/Hedge-Edge-Front-end`

### 1. Bump Version

```bash
python Business/STRATEGY/executions/Product/app_deployer.py --action bump --bump patch
```

Semver rules:
- **patch** (1.0.4 → 1.0.5): bug fixes, minor improvements
- **minor** (1.0.4 → 1.1.0): new features, non-breaking
- **major** (1.0.4 → 2.0.0): breaking changes to hedge behaviour

### 2. Build Installer

```bash
python Business/STRATEGY/executions/Product/app_deployer.py --action build
```

Runs `npm run electron:compile` then `npm run electron:build:win`.
Outputs to `release/`: `.exe` (~100 MB), `.blockmap`, `latest.yml`.

### 3. Push & Release

```bash
python Business/STRATEGY/executions/Product/app_deployer.py --action release --notes "Changelog text"
```

Commits, pushes, creates the GitHub Release with all three artifacts.

### 4. Verify

```bash
python Business/STRATEGY/executions/Product/app_deployer.py --action verify
```

Lists recent releases and confirms artifact presence.

### 5. Full Pipeline (all-in-one)

```bash
python Business/STRATEGY/executions/Product/app_deployer.py --action deploy --bump patch --notes "v1.0.6 — bug fixes"
```

Runs steps 1-4 sequentially.

## Critical Rules

1. **`latest.yml` must always exist in the latest GitHub Release** — `electron-updater` reads it.
   If you publish a non-app release (e.g. MT5 EAs only), you must still include the current
   `latest.yml` + installer artifacts so the auto-updater doesn't 404.

2. **Never skip the blockmap** — it enables delta updates (faster downloads for users).

3. **Never release during London/NY overlap** (08:00-12:00 EST Mon-Fri) or on Fridays.

4. **Preferred window**: Tuesday-Thursday, 17:00-20:00 EST (after NY close, before Asia open).

5. **Hotfix exception**: P0 hotfixes can ship anytime but require double monitoring.

## Rollback Procedure

If a release is broken:
1. Delete the bad release: `gh release delete v<bad> --repo Micha12344f/Hedge-Edge-App`
2. Re-upload the last known good `latest.yml` + installer to the previous release tag
3. Notify users via Discord #updates channel
