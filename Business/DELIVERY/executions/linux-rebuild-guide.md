# Full Linux Rebuild — AgentForge Server

> **Goal**: Wipe the current Windows installation on the physical Lenovo server and replace it with Ubuntu Server 24.04 LTS, Docker Engine, and Cloudflare Tunnel — ready for MCP container deployments.

---

## Current Server Inventory

| Spec | Value |
|------|-------|
| Hardware | Lenovo 82RK |
| CPU | Intel Core i3-1215U (12th Gen, 6 cores) |
| RAM | ~3.7 GB |
| Disk | ~117 GB SSD |
| Current OS | Windows (to be wiped) |
| Tunnel | cloudflared 2026.3.0, dashboard-managed via Cloudflare One |
| SSH user | hedgebot |
| Hostname | ssh.hedgedge.info (via Cloudflare Access) |

**Data status**: Safe to wipe — nothing to preserve.

---

## What You Need

- A **USB flash drive** (4 GB minimum, 8+ GB recommended)
- Physical access to the Lenovo server
- A separate computer (your Windows PC) to create the USB installer
- Your **Cloudflare One dashboard** login (to reconfigure the tunnel)

---

## Phase 1 — Download Ubuntu Server ISO

### Source: Canonical (official)
- **URL**: https://ubuntu.com/download/server
- **Version**: Ubuntu Server 24.04.4 LTS (Noble Numbat)
- **Direct download**: https://ubuntu.com/download/server/thank-you?version=24.04.4&architecture=amd64&lts=true
- **File size**: ~3 GB
- **Support**: 5 years of free security updates (until April 2029), extendable to 15 years with Ubuntu Pro

**Why 24.04 LTS?**
- Long-term support — stable, no surprise breakage
- Docker officially supports it (confirmed on docs.docker.com)
- Linux 6.8 kernel with modern hardware support (including 12th Gen Intel)

### Verify the download (recommended)

After downloading the ISO, verify it using the SHA256 checksum published by Canonical:

1. Go to https://releases.ubuntu.com/24.04/ and find the `SHA256SUMS` file
2. Open PowerShell on your PC and run:
   ```powershell
   Get-FileHash .\ubuntu-24.04.4-live-server-amd64.iso -Algorithm SHA256
   ```
3. Compare the output hash with the one in Canonical's `SHA256SUMS` file — they must match exactly

---

## Phase 2 — Create Bootable USB with Rufus

### Source: Rufus (official)
- **URL**: https://rufus.ie
- **Version**: Rufus 4.13 (latest as of Feb 2026)
- **Direct download**: https://rufus.ie — click "rufus-4.13.exe" (Standard, 1.9 MB)
- **License**: GPLv3 open source
- **Signature**: Digitally signed by "Akeo Consulting"

### Steps

1. **Download Rufus** from https://rufus.ie — run the .exe directly (no install needed)
2. **Insert your USB drive** into your Windows PC
3. In Rufus:
   - **Device**: Select your USB drive
   - **Boot selection**: Click SELECT → browse to the Ubuntu ISO you downloaded
   - **Partition scheme**: **GPT** (this Lenovo uses UEFI)
   - **Target system**: **UEFI (non CSM)**
   - **File system**: Leave as FAT32 (default)
   - **Volume label**: Leave as-is or type "Ubuntu Server"
4. Click **START**
5. If prompted, choose "Write in ISO Image mode" → OK
6. Wait for completion (a few minutes)
7. **Safely eject** the USB drive

---

## Phase 3 — Install Ubuntu Server on the Lenovo

### Boot from USB

1. **Plug the USB** into the Lenovo server
2. **Power on** (or restart) the machine
3. **Enter BIOS/Boot menu**: Press **F12** (Lenovo boot menu) or **F2** (BIOS setup) repeatedly during startup
4. Select the USB drive from the boot menu
5. If you see "Try or Install Ubuntu Server" — select it

### Ubuntu Server Installer

The installer is text-based (no GUI needed — this is a server). Follow these steps:

1. **Language**: English
2. **Keyboard**: Select your layout
3. **Installation type**: "Ubuntu Server" (not minimized)
4. **Network**: The installer will auto-detect your Ethernet/WiFi. Confirm your network connection is active (you need internet for Phase 4+)
5. **Proxy**: Leave blank (unless you use a corporate proxy)
6. **Mirror**: Leave default (archive.ubuntu.com)
7. **Storage**:
   - Select "Use an entire disk"
   - Select the 117 GB SSD
   - Confirm "destructive action" — this wipes Windows
   - **Do NOT enable LVM** unless you specifically want it (simpler without)
8. **Profile setup**:
   - Your name: (your name)
   - Server name: `agentforge` (or `server` to keep it the same)
   - Username: `hedgebot` ← **keep the same username for SSH consistency**
   - Password: Choose a strong password
9. **Ubuntu Pro**: Skip (select "Skip for now")
10. **SSH**: ✅ **Install OpenSSH server** ← CRITICAL — check this box
    - Do NOT import SSH keys from GitHub/Launchpad (we'll set up keys manually)
11. **Featured snaps**: Skip all — we'll install Docker via the official apt repo (more reliable than snap)
12. **Wait** for installation to complete
13. **Remove USB** when prompted, then **reboot**

### First boot

After reboot, you'll see a login prompt. Log in with:
```
Username: hedgebot
Password: (the password you set)
```

### Verify the system

```bash
# Confirm OS
cat /etc/os-release

# Confirm hostname
hostname

# Confirm network (note the IP address — you need this)
ip addr show

# Confirm SSH is running
sudo systemctl status ssh
```

**Write down the local IP address** — you'll need it for Cloudflare tunnel setup.

---

## Phase 4 — Harden the Server (Security Baseline)

Run these commands after first login:

```bash
# Update all packages to latest
sudo apt update && sudo apt upgrade -y

# Enable automatic security updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
# Select "Yes" when prompted

# Set up firewall (UFW) — allow SSH only
sudo ufw allow OpenSSH
sudo ufw enable
# Type "y" to confirm

# Verify firewall
sudo ufw status

# Disable root login via SSH (should already be disabled, but verify)
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

### Set up SSH key authentication (from your Windows PC)

On your **Windows PC**, open PowerShell:

```powershell
# If you don't have an SSH key yet:
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy your public key to the server (replace IP with the server's local IP)
# You'll need to be on the same local network for this step
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh hedgebot@<SERVER_LOCAL_IP> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

Then verify key login works:
```powershell
ssh hedgebot@<SERVER_LOCAL_IP>
```

### Optional: Disable password authentication (after key login works)

```bash
# On the server:
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

---

## Phase 5 — Install Docker Engine

### Source: Docker official documentation
- **URL**: https://docs.docker.com/engine/install/ubuntu/
- **Supported**: Ubuntu 24.04 (Noble) on amd64 ✅

### Install via official apt repository (recommended by Docker)

```bash
# 1. Add Docker's official GPG key
sudo apt update
sudo apt install ca-certificates curl -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# 2. Add the Docker apt repository
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update

# 3. Install Docker Engine, CLI, containerd, Compose, and Buildx
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# 4. Verify Docker is running
sudo systemctl status docker

# 5. Test with hello-world
sudo docker run hello-world
```

### Post-install: Run Docker without sudo

```bash
# Add hedgebot to the docker group
sudo usermod -aG docker hedgebot

# Log out and back in for the group change to take effect
exit
# Then SSH back in and verify:
docker run hello-world
```

### Verify Docker components

```bash
docker --version
docker compose version
docker buildx version
```

**Expected output** (versions may be newer):
```
Docker version 29.x.x
Docker Compose version v5.x.x
Docker Buildx version v0.x.x
```

---

## Phase 6 — Install and Configure Cloudflare Tunnel

### Source: Cloudflare official documentation
- **Install**: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
- **Tutorial**: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/
- **GitHub**: https://github.com/cloudflare/cloudflared (open source)

### Option A: Reinstall the SAME tunnel (recommended)

Since your tunnel is **dashboard-managed**, you can connect the new Linux machine to the **same tunnel**:

1. Log in to **Cloudflare One** → https://one.dash.cloudflare.com/
2. Go to **Networks → Connectors → Cloudflare Tunnels**
3. Find your existing tunnel (the one that served `ssh.hedgedge.info`)
4. Click on it → **Configure**
5. Under the connectors tab, you'll see the old Windows connector (it will show as "inactive" since we wiped Windows)
6. The dashboard will show an **install command** — select **Linux** → **Debian/Ubuntu** as the environment
7. **Copy the install command** — it will look something like:
   ```bash
   curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared.deb
   sudo cloudflared service install <YOUR_TUNNEL_TOKEN>
   ```
8. **Run these commands** on the new Ubuntu server

### Option B: Install cloudflared manually, then connect

```bash
# Download the .deb package from Cloudflare's official release
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Install it
sudo dpkg -i cloudflared.deb

# Verify
cloudflared --version

# Install as a system service using your dashboard tunnel token
# (get the token from Cloudflare One dashboard as described above)
sudo cloudflared service install <YOUR_TUNNEL_TOKEN>

# Verify the service is running
sudo systemctl status cloudflared
```

### Configure the tunnel routes in the dashboard

After the connector comes online:

1. In **Cloudflare One → Networks → Tunnels** → your tunnel → **Configure**
2. Under **Public Hostnames**, verify/add:
   - **Hostname**: `ssh.hedgedge.info`
   - **Service**: `ssh://localhost:22`
3. Save

### Verify SSH through Cloudflare tunnel

On your **Windows PC**:
```powershell
ssh hedge-vps "hostname && cat /etc/os-release | head -3"
```

Expected output should show the Ubuntu hostname and OS info.

---

## Phase 7 — Allow Docker Ports Through Firewall (for MCP containers)

```bash
# Note: Docker manages its own iptables rules for published container ports.
# UFW rules alone won't block Docker-published ports.
# For local-only containers (behind Cloudflare tunnel), no UFW changes needed.

# If you need to expose a port publicly (e.g., for health checks):
# sudo ufw allow 8080/tcp comment "MCP container health"

# Verify Docker networking works
docker run --rm -p 8080:80 nginx:alpine &
curl -s http://localhost:8080 | head -5
docker stop $(docker ps -q --filter ancestor=nginx:alpine)
```

---

## Phase 8 — Install Python (for MCP server development)

```bash
# Ubuntu 24.04 ships with Python 3.12, verify it:
python3 --version

# Install pip and venv
sudo apt install python3-pip python3-venv -y

# Verify
pip3 --version
```

---

## Post-Rebuild Validation Checklist

Run this script to validate everything is working:

```bash
echo "=== OS ==="
cat /etc/os-release | head -4

echo -e "\n=== Hostname ==="
hostname

echo -e "\n=== CPU ==="
lscpu | grep "Model name"

echo -e "\n=== Memory ==="
free -h | head -2

echo -e "\n=== Disk ==="
df -h /

echo -e "\n=== Docker ==="
docker --version
docker compose version

echo -e "\n=== Docker Test ==="
docker run --rm hello-world 2>&1 | head -3

echo -e "\n=== Cloudflared ==="
cloudflared --version
sudo systemctl status cloudflared --no-pager | head -5

echo -e "\n=== SSH ==="
sudo systemctl status ssh --no-pager | head -5

echo -e "\n=== Firewall ==="
sudo ufw status

echo -e "\n=== Python ==="
python3 --version
pip3 --version
```

**All checks should pass before proceeding to MCP container deployments.**

---

## Official Source Links (All Reputable)

| What | Source | URL |
|------|--------|-----|
| Ubuntu Server 24.04 LTS ISO | Canonical (official) | https://ubuntu.com/download/server |
| Ubuntu ISO checksums | Canonical (official) | https://releases.ubuntu.com/24.04/ |
| Rufus USB creator | rufus.ie (official, GPLv3) | https://rufus.ie |
| Docker Engine for Ubuntu | Docker Inc. (official) | https://docs.docker.com/engine/install/ubuntu/ |
| Docker post-install steps | Docker Inc. (official) | https://docs.docker.com/engine/install/linux-postinstall/ |
| cloudflared downloads | Cloudflare (official) | https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ |
| Cloudflare tunnel setup | Cloudflare (official) | https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/ |
| cloudflared source code | Cloudflare (GitHub, Apache 2.0) | https://github.com/cloudflare/cloudflared |
| Ubuntu security updates | Canonical (official) | https://ubuntu.com/security |
| UFW firewall docs | Ubuntu (official) | https://ubuntu.com/server/docs/firewalls |

---

## After the Rebuild — What Changes in the Workspace

Once the server is running Ubuntu, the following workspace files need updating:

1. **`.env`** — `SSH_HOST` stays the same (Cloudflare tunnel handles routing). No change needed if using the same tunnel.
2. **`~/.ssh/config`** — The `hedge-vps` alias stays the same (it points to `ssh.hedgedge.info` via cloudflared proxy). No change needed.
3. **`Business/engineering/directives/remote-server-access.md`** — Update to reflect Linux host instead of Windows.
4. **`Business/engineering/directives/dockerized-mcp-deployment.md`** — Remove the "Windows host gate" since Docker now works natively on Linux.

---

## Estimated Time

| Phase | Time |
|-------|------|
| Download Ubuntu ISO | 5–15 min (depending on internet) |
| Create USB with Rufus | 3–5 min |
| Install Ubuntu | 10–15 min |
| Harden + SSH keys | 5–10 min |
| Install Docker | 5 min |
| Install cloudflared + tunnel | 5–10 min |
| Validation | 5 min |
| **Total** | **~45–60 min** |
