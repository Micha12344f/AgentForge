#!/usr/bin/env bash
# post_rebuild_check.sh — Run on the new Ubuntu server after the Linux rebuild.
# Validates that all required services are healthy for MCP container deployments.
# Usage: bash post_rebuild_check.sh
set -euo pipefail

PASS=0
FAIL=0
report() {
    local label="$1" status="$2"
    if [ "$status" = "ok" ]; then
        echo "[PASS] $label"
        ((PASS++))
    else
        echo "[FAIL] $label — $status"
        ((FAIL++))
    fi
}

echo "========================================"
echo " AgentForge Post-Rebuild Validation"
echo "========================================"
echo ""

# 1. OS check
if grep -q "24.04" /etc/os-release 2>/dev/null; then
    report "Ubuntu 24.04 LTS installed" "ok"
else
    report "Ubuntu 24.04 LTS installed" "unexpected OS: $(grep PRETTY_NAME /etc/os-release 2>/dev/null || echo unknown)"
fi

# 2. Hostname
HOST=$(hostname)
report "Hostname is set ($HOST)" "ok"

# 3. SSH service
if systemctl is-active --quiet ssh; then
    report "SSH service running" "ok"
else
    report "SSH service running" "ssh is not active"
fi

# 4. UFW firewall
if sudo ufw status | grep -q "Status: active"; then
    report "UFW firewall active" "ok"
else
    report "UFW firewall active" "ufw is not active"
fi

# 5. Docker Engine
if docker version > /dev/null 2>&1; then
    DOCKER_VER=$(docker --version)
    report "Docker Engine reachable ($DOCKER_VER)" "ok"
else
    report "Docker Engine reachable" "docker version failed"
fi

# 6. Docker Compose
if docker compose version > /dev/null 2>&1; then
    COMPOSE_VER=$(docker compose version --short)
    report "Docker Compose available (v$COMPOSE_VER)" "ok"
else
    report "Docker Compose available" "docker compose not found"
fi

# 7. Docker hello-world
if docker run --rm hello-world > /dev/null 2>&1; then
    report "Docker can run containers" "ok"
else
    report "Docker can run containers" "hello-world failed"
fi

# 8. Docker group membership
if groups | grep -q docker; then
    report "User in docker group (no sudo needed)" "ok"
else
    report "User in docker group" "$(whoami) not in docker group"
fi

# 9. cloudflared installed
if command -v cloudflared > /dev/null 2>&1; then
    CF_VER=$(cloudflared --version)
    report "cloudflared installed ($CF_VER)" "ok"
else
    report "cloudflared installed" "cloudflared not found"
fi

# 10. cloudflared service
if sudo systemctl is-active --quiet cloudflared; then
    report "cloudflared service running" "ok"
else
    report "cloudflared service running" "cloudflared service is not active"
fi

# 11. Python3
if command -v python3 > /dev/null 2>&1; then
    PY_VER=$(python3 --version)
    report "Python3 available ($PY_VER)" "ok"
else
    report "Python3 available" "python3 not found"
fi

# 12. pip3
if command -v pip3 > /dev/null 2>&1; then
    report "pip3 available" "ok"
else
    report "pip3 available" "pip3 not found"
fi

# 13. Automatic security updates
if dpkg -l unattended-upgrades 2>/dev/null | grep -q "^ii"; then
    report "Unattended upgrades installed" "ok"
else
    report "Unattended upgrades installed" "package not installed"
fi

echo ""
echo "========================================"
echo " Results: $PASS passed, $FAIL failed"
echo "========================================"

if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "Fix the failed checks before deploying MCP containers."
    exit 1
else
    echo ""
    echo "All checks passed — server is ready for MCP container deployments."
    exit 0
fi
