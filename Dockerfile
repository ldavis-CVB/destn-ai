FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard/ dashboard/
COPY pipeline/ pipeline/
COPY data/.gitkeep data/

CMD ["python", "-m", "streamlit", "run", "dashboard/app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.headless", "true", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false"]
