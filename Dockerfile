# Dockerfile
FROM python:3.10-slim

# Avoid Python buffering
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["streamlit", "run", "main.py", "--server.port=8000", "--server.address=0.0.0.0", "--server.fileWatcherType=none"]
