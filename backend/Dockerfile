FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download TextBlob corpora
RUN python -c "import textblob; textblob.download_corpora(quiet=True)" 2>/dev/null || true

COPY . .

EXPOSE 8000
