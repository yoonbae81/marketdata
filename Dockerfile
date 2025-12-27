FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make scripts executable
RUN find src scripts -type f \( -name "*.py" -o -name "*.sh" \) -exec chmod +x {} + 2>/dev/null || true
RUN chmod +x entrypoint.sh

# Create log directory and data directory
RUN mkdir -p /var/log/app /data

# Set environment variables
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "entrypoint.sh"]
