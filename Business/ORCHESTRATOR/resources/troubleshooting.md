# Troubleshooting — Hedge Edge Deployment

Common issues encountered during the deployment workflow and how to fix them.

---

## Build Issues

### `electron:compile` fails with TypeScript errors

**Cause**: Type errors in `electron/*.ts` files.

**Fix**: Check the error output, fix the TS issues, then re-run:
```powershell
npm run electron:compile 2>&1
```

### `electron:build:win` fails

**Cause**: Usually a missing dependency or Vite build error.

**Fix**:
1. Run `npm install` to ensure all deps are present
2. Run `npm run electron:compile` separately first to isolate TS issues
3. Then run `npm run electron:build:win`

### Installer output is 0 bytes or missing

**Cause**: Build silently failed or wrote to a different directory.

**Fix**: Check `release/builder-debug.yml` for the actual error. Also inspect `release/builder-effective-config.yaml` for the resolved config.

---

## Git / Push Issues

### `git push origin main` rejected (non-fast-forward)

**Cause**: Remote has commits your local branch doesn't have.

**Fix**:
```powershell
git pull --no-edit origin main
git push origin main
```

### Push hangs or times out

**Cause**: Large `.exe` file is being tracked by git.

**Fix**: Ensure `release/` is in `.gitignore`. The installer should never be committed — it's uploaded to GitHub Releases separately.

---

## GitHub CLI Issues

### `gh: command not found` or `gh auth` not logged in

**Fix**:
```powershell
# Install gh (if missing)
winget install GitHub.cli

# Authenticate
gh auth login --web
```
Follow the device code flow in your browser.

### `gh release create` fails with "release already exists"

**Cause**: A release with that tag already exists on GitHub.

**Fix**: Either delete the old release first:
```powershell
gh release delete v<version> --repo Micha12344f/Hedge-Edge-App --yes
git push origin :refs/tags/v<version>
```
Or bump to the next version.

### `gh release create` fails with "Not Found" (404)

**Cause**: The repo doesn't exist or gh is authenticated as the wrong user.

**Fix**:
```powershell
gh auth status
gh repo view Micha12344f/Hedge-Edge-App
```

---

## Auto-Updater Issues

### `ENOENT: dev-app-update.yml` in dev mode

**Cause**: `electron-updater` with `forceDevUpdateConfig = true` needs this file at the project root.

**Fix**: Create `dev-app-update.yml` in the frontend root:
```yaml
provider: github
owner: Micha12344f
repo: Hedge-Edge-App
```

### Updater says "No update available" even though a newer release exists

**Cause**: The app's `package.json` version matches or exceeds the latest release version.

**Fix**: Ensure the GitHub Release version is higher than the app's current version. Check:
```powershell
# App version
node -e "console.log(require('./package.json').version)"

# Latest GitHub release
gh release list --repo Micha12344f/Hedge-Edge-App --limit 1
```

### Updater error: "Cannot find latest.yml"

**Cause**: `latest.yml` was not uploaded to the GitHub Release.

**Fix**: Upload it manually:
```powershell
gh release upload v<version> "release/latest.yml" --repo Micha12344f/Hedge-Edge-App
```

---

## Electron Dev Mode Issues

### App crashes with `ERR_FAILED` loading localhost

**Cause**: Vite dev server isn't running when Electron tries to load the page.

**Fix**: The `electron:dev` script uses `concurrently` to start Vite and Electron together. If it fails:
1. Kill all node/electron processes: `Get-Process -Name "node","electron" -ErrorAction SilentlyContinue | Stop-Process -Force`
2. Re-run: `npm run electron:dev`

### License key not persisting across restarts

**Cause**: `LicenseStore` was initialized before `app.whenReady()`, so `safeStorage.isEncryptionAvailable()` returned false.

**Fix**: This was fixed in v1.0.4 — the `LicenseStore.initialize()` method is now called after `app.whenReady()` completes. If it regresses, check `electron/license-store.ts` and ensure the singleton doesn't call `safeStorage` in the constructor.
