FROM python:3.11-slim

# Install system-level cron daemon
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Invalidate cache only when dependencies change
COPY 01-cron/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy internal shared infrastructure and project contexts
COPY shared/ /app/shared/
COPY 01-cron/main.py /app/01-cron/main.py

# Inject crontab directive ensuring runtime environments are sourced correctly
RUN echo "* * * * * . /etc/environment; python /app/01-cron/main.py > /proc/1/fd/1 2>&1" > /etc/cron.d/weather-cron
RUN chmod 0644 /etc/cron.d/weather-cron
RUN crontab /etc/cron.d/weather-cron

RUN touch /var/log/cron.log

# Entrypoint script mapping system envs into cron context to circumvent shell isolation
RUN echo '#!/bin/sh\nprintenv | grep -v "no_proxy" >> /etc/environment\ncron && tail -f /var/log/cron.log' > /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
