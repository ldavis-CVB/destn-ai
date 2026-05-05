FROM python:3.11-slim

WORKDIR /app

# Install cron for scheduled probe + GA4 jobs
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m textblob.download_corpora

COPY dashboard/ dashboard/
COPY pipeline/ pipeline/
COPY data/.gitkeep data/

# Install crontab
COPY crontab /etc/cron.d/destn-ai
RUN chmod 0644 /etc/cron.d/destn-ai

EXPOSE 8080

COPY start.sh .
RUN sed -i 's/\r//' start.sh && chmod +x start.sh

CMD ["/bin/sh", "start.sh"]
