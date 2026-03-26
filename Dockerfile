# ─────────────────────────────────────────────────────────────────────
# Hedge Edge — Email Send Service
# Build context: repository root
# Railway service: shared/Email-Send-Service (railway.toml → dockerfilePath = "Dockerfile")
# ─────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# ── Dependencies (cached layer) ──
COPY shared/Email-Send-Service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ── Service entry points ──
COPY shared/Email-Send-Service/email_send.py ./email_send.py
COPY shared/Email-Send-Service/main.py       ./main.py

# ── Workspace shared modules ──
# All shared/*.py files that email_send + main + their transitive deps need
COPY shared/notion_client.py   ./shared/notion_client.py
COPY shared/env_loader.py      ./shared/env_loader.py
COPY shared/alerting.py        ./shared/alerting.py
COPY shared/discord_client.py  ./shared/discord_client.py
COPY shared/supabase_client.py ./shared/supabase_client.py

# ── Service-local resend client (no workspace equivalent) ──
COPY shared/Email-Send-Service/shared/resend_client.py ./shared/resend_client.py

# Make `shared` a proper Python package
RUN touch /app/shared/__init__.py

# ── Runtime config ──
# Env vars are injected by Railway — no .env file needed in the image
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
