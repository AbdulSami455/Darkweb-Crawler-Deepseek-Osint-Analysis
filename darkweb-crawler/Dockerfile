# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive
ENV HOST=0.0.0.0
ENV PORT=8000
ENV RELOAD=false
ENV TOR_SOCKS_HOST=host.docker.internal
ENV TOR_SOCKS_PORT=9050

# Install system dependencies including Tor
RUN apt-get update && apt-get install -y \
    tor \
    curl \
    wget \
    git \
    build-essential \
    libyara-dev \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create tor user and configure Tor
RUN useradd -m -d /home/tor tor && \
    chown -R tor:tor /var/lib/tor && \
    chown -R tor:tor /var/log/tor

# Configure Tor (but we'll use host Tor instead)
RUN echo "# Tor configuration - using host Tor instead" > /etc/tor/torrc && \
    echo "# SocksPort 9050" >> /etc/tor/torrc && \
    echo "# DataDirectory /var/lib/tor" >> /etc/tor/torrc && \
    echo "# Log notice file /var/log/tor/notices.log" >> /etc/tor/torrc && \
    echo "# RunAsDaemon 0" >> /etc/tor/torrc && \
    echo "# User tor" >> /etc/tor/torrc

# Create necessary directories
RUN mkdir -p /var/lib/tor /var/log/tor /app/logs /app/torcrawl/output && \
    chown -R tor:tor /var/lib/tor /var/log/tor && \
    chown -R root:root /app

# Expose ports
EXPOSE 8000 9050

# Set default command to run the server directly
CMD ["python", "server.py"]
