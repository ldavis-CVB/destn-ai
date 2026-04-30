FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m textblob.download_corpora

COPY dashboard/ dashboard/
COPY pipeline/ pipeline/
COPY data/.gitkeep data/

EXPOSE 8080

CMD ["/bin/sh", "-c", "echo PORT=$PORT && python -c 'import streamlit,pandas,plotly,textblob,openai; print(\"imports OK\")' 2>&1 && python -m streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false 2>&1"]
