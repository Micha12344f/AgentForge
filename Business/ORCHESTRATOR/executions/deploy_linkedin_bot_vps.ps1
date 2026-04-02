$ErrorActionPreference = "Stop"

$workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$remoteRootName = "linkedin-leads-bot"
$remoteWindowsRoot = "C:\Users\hedgebot.Server\$remoteRootName"
$remoteWslRoot = "/mnt/c/Users/hedgebot.Server/$remoteRootName"
$composeFile = "Business/GROWTH/executions/Marketing/docker-compose.linkedin-bot.yml"
$rootEnvPath = Join-Path $workspaceRoot ".env"
$botEnvTempPath = Join-Path ([System.IO.Path]::GetTempPath()) "linkedin-bot.env"

$requiredBotEnvKeys = @(
    "LINKEDIN_EMAIL",
    "LINKEDIN_PASSWORD",
    "MAHMUD_LINKEDIN_EMAIL",
    "MAHMUD_LINKEDIN_PASSWORD"
)

$optionalBotEnvKeys = @(
    "NOTION_API_KEY",
    "NOTION_TOKEN",
    "DISCORD_ALERTS_CHANNEL_ID",
    "DISCORD_BOT_TOKEN",
    "DISCORD_WEBHOOK_URL"
)

$botEnvKeys = $requiredBotEnvKeys + $optionalBotEnvKeys

$marketingDir = Join-Path $workspaceRoot "Business\GROWTH\executions\Marketing"
$sharedDir = Join-Path $workspaceRoot "shared"

$marketingFiles = @(
    "linkedin_scraper.py",
    "linkedin_leads_workflow.py",
    "linkedin_bot_service.py",
    "linkedin_bot_requirements.txt",
    "Dockerfile.linkedin-bot",
    "docker-compose.linkedin-bot.yml",
    ".linkedin_session.json",
    ".linkedin_session_mahmud.json"
)

$sharedFiles = @(
    "notion_client.py",
    "env_loader.py",
    "alerting.py"
)

$remoteDirs = @(
    "$remoteWindowsRoot\Business\GROWTH\executions\Marketing",
    "$remoteWindowsRoot\shared"
)

$dirCommand = ($remoteDirs | ForEach-Object { "New-Item -ItemType Directory -Force -Path '$_' | Out-Null" }) -join "; "

Write-Host "[deploy] Creating remote directories..."
& ssh hedge-vps "powershell -NoProfile -Command \"$dirCommand\""
if ($LASTEXITCODE -ne 0) { throw "Failed to create remote directories." }

$selectedEnvLines = New-Object System.Collections.Generic.List[string]
$seenBotEnvKeys = New-Object 'System.Collections.Generic.HashSet[string]'

foreach ($line in Get-Content $rootEnvPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line.TrimStart().StartsWith("#")) { continue }

    $separatorIndex = $line.IndexOf("=")
    if ($separatorIndex -lt 1) { continue }

    $key = $line.Substring(0, $separatorIndex).Trim()
    if ($botEnvKeys -contains $key) {
        $selectedEnvLines.Add($line)
        $null = $seenBotEnvKeys.Add($key)
    }
}

$missingRequiredKeys = $requiredBotEnvKeys | Where-Object { -not $seenBotEnvKeys.Contains($_) }
if ($missingRequiredKeys.Count -gt 0) {
    throw "Missing required bot env keys: $($missingRequiredKeys -join ', ')"
}

if (-not ($seenBotEnvKeys.Contains("NOTION_API_KEY") -or $seenBotEnvKeys.Contains("NOTION_TOKEN"))) {
    throw "Missing required bot env key: NOTION_API_KEY or NOTION_TOKEN"
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($botEnvTempPath, ($selectedEnvLines -join [Environment]::NewLine), $utf8NoBom)

Write-Host "[deploy] Copying bot env..."
& scp $botEnvTempPath "hedge-vps:$remoteRootName/.env.linkedin-bot"
if ($LASTEXITCODE -ne 0) { throw "Failed to copy bot env file." }

if (Test-Path $botEnvTempPath) {
    Remove-Item $botEnvTempPath -Force
}

foreach ($file in $marketingFiles) {
    Write-Host "[deploy] Copying Marketing/$file"
    & scp (Join-Path $marketingDir $file) "hedge-vps:$remoteRootName/Business/GROWTH/executions/Marketing/"
    if ($LASTEXITCODE -ne 0) { throw "Failed to copy Marketing/$file" }
}

foreach ($file in $sharedFiles) {
    Write-Host "[deploy] Copying shared/$file"
    & scp (Join-Path $sharedDir $file) "hedge-vps:$remoteRootName/shared/"
    if ($LASTEXITCODE -ne 0) { throw "Failed to copy shared/$file" }
}

Write-Host "[deploy] Docker Compose build + up..."
& ssh hedge-vps wsl -d Ubuntu --cd $remoteWslRoot docker compose -f $composeFile up -d --build
if ($LASTEXITCODE -ne 0) { throw "Failed to build/start linkedin bot container." }

Write-Host "[deploy] Docker Compose status..."
& ssh hedge-vps wsl -d Ubuntu --cd $remoteWslRoot docker compose -f $composeFile ps
if ($LASTEXITCODE -ne 0) { throw "Failed to read container status." }

Write-Host "[deploy] Recent logs..."
& ssh hedge-vps wsl -d Ubuntu --cd $remoteWslRoot docker compose -f $composeFile logs --tail=120 linkedin-leads-bot
if ($LASTEXITCODE -ne 0) { throw "Failed to read container logs." }
