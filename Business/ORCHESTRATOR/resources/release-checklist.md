# Release Checklist

Use this checklist before and after every Hedge Edge release.

---

## Pre-Release

- [ ] All features/fixes committed to `main`
- [ ] `npm run electron:compile` succeeds with no errors
- [ ] App launches in dev mode (`npm run electron:dev`) without crashes
- [ ] License key persistence works (survives app restart)
- [ ] Version bumped in `package.json` (no duplicate with existing releases)
- [ ] `gh auth status` shows authenticated as `Micha12344f`
- [ ] `git status` is clean (no uncommitted files that shouldn't ship)
- [ ] `dev-app-update.yml` exists at project root with correct provider config

## Build

- [ ] `npm run electron:build:win` completes without errors
- [ ] `release/HedgeEdge-<version>-win-x64.exe` exists (~100 MB)
- [ ] `release/HedgeEdge-<version>-win-x64.exe.blockmap` exists
- [ ] `release/latest.yml` exists and shows correct version

## Publish

- [ ] Changes committed with message `release: v<version>`
- [ ] `git push origin main` succeeds
- [ ] `gh release create v<version>` succeeds with 3 assets attached
- [ ] `gh release list` shows the new release

## Post-Release Verification

- [ ] Release page on GitHub shows the correct version and 3 assets
- [ ] Download the `.exe` from GitHub and verify it installs
- [ ] Auto-updater detects the new version (test from an older installed version)
- [ ] No broken/dead links in release notes

## Rollback (if needed)

If the release is broken:

```powershell
# Delete the GitHub release
gh release delete v<version> --repo Micha12344f/Hedge-Edge-App --yes

# Delete the git tag
git tag -d v<version>
git push origin :refs/tags/v<version>

# Revert the version bump commit
git revert HEAD
git push origin main
```
