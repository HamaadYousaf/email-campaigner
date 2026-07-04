FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies (optional but safe for networking/libs)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY . .

# Expose Prometheus metrics port (for clarity)
EXPOSE 8001

# Run worker
CMD ["python", "main.py"]