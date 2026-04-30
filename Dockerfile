FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m textblob.download_corpora

COPY dashboard/ dashboard/
COPY pipeline/ pipeline/
COPY data/.gitkeep data/

EXPOSE 8080

CMD ["/bin/sh", "-c", "echo '==> PORT='$PORT && python -c 'import streamlit; print(\"streamlit\", streamlit.__version__)' && python -c 'import sys; sys.path.insert(0,\"pipeline\"); from queries import QUERIES; print(\"queries OK\", len(QUERIES))' && echo '==> Starting Streamlit...' && python -m streamlit run dashboard/app.py --server.port ${PORT:-8080} --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false 2>&1"]
