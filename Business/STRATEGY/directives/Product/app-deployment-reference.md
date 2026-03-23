# App Deployment Reference — Product

## GitHub Repository

- **Repo**: `Micha12344f/Hedge-Edge-App`
- **URL**: https://github.com/Micha12344f/Hedge-Edge-App

## Workspace Location

- **Repo clone**: `Business/STRATEGY/resources/Product/Hedge-Edge-App`
- **Desktop app root**: `Business/STRATEGY/resources/Product/Hedge-Edge-App/Hedge-Edge-Beta/Hedge-Edge-Front-end`

## Release Artifacts

Every GitHub Release marked as "Latest" MUST contain these files for the auto-updater to work:

| File | Purpose |
|------|---------|
| `HedgeEdge-<version>-win-x64.exe` | Windows NSIS installer (~100 MB) |
| `HedgeEdge-<version>-win-x64.exe.blockmap` | Delta update support (~115 KB) |
| `latest.yml` | `electron-updater` manifest (version, sha512, size, URL) |

## Auto-Updater Flow

1. User's app calls `autoUpdater.checkForUpdates()`
2. electron-updater fetches `latest.yml` from the **latest** GitHub Release
3. Compares `latest.yml` version against installed version
4. If newer, downloads the `.exe` (using `.blockmap` for delta if available)
5. Prompts user to install and restart

## Common Pitfall

If a non-app release (e.g. MT5 Experts only) is published as the latest release
WITHOUT `latest.yml`, users will get a **404 error** when checking for updates.

**Fix**: Always include the current `latest.yml` + installer in every release, or
use a separate release tag for non-app assets.

## Build Stack

| Component | Tool |
|-----------|------|
| Frontend | Vite + React |
| Desktop shell | Electron |
| TypeScript compile | `npm run electron:compile` |
| Installer build | `electron-builder` via `npm run electron:build:win` |
| Versioning | `package.json` version field (semver) |

## Verified Deploy Command

```bash
python Business/STRATEGY/executions/Product/app_deployer.py --action deploy --bump patch --notes "v1.0.6"
```
