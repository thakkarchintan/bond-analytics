FROM python:3.11-slim

WORKDIR /app

# System deps for grpcio (firebase-admin), lxml (sumy), and SSL certs
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libssl-dev \
    ca-certificates \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps as a separate layer — cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . /app

ENV PYTHONUNBUFFERED=1

EXPOSE 8501

# To activate Playwright (scrap.py) in future, add before COPY:
#   RUN playwright install --with-deps chromium
CMD ["python", "-m", "streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
