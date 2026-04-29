FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY dashboard/ dashboard/
COPY pipeline/ pipeline/
COPY data/.gitkeep data/

EXPOSE 8501

CMD streamlit run dashboard/app.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true
