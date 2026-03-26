FROM python:3.12-slim

WORKDIR /app

# Install service dependencies first for better layer caching.
COPY shared/Email-Send-Service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy service entrypoints.
COPY shared/Email-Send-Service/email_send.py ./email_send.py
COPY shared/Email-Send-Service/main.py ./main.py

# Copy the workspace shared modules required by the email service.
COPY shared/notion_client.py ./shared/notion_client.py
COPY shared/env_loader.py ./shared/env_loader.py
COPY shared/alerting.py ./shared/alerting.py
COPY shared/discord_client.py ./shared/discord_client.py
COPY shared/supabase_client.py ./shared/supabase_client.py
COPY shared/resend_client.py ./shared/resend_client.py

# Make shared importable as a package inside the image.
RUN touch /app/shared/__init__.py

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
