FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m textblob.download_corpora

COPY dashboard/ dashboard/
COPY pipeline/ pipeline/
COPY data/.gitkeep data/

EXPOSE 8080

COPY start.sh .
RUN sed -i 's/\r//' start.sh && chmod +x start.sh

CMD ["/bin/sh", "start.sh"]
