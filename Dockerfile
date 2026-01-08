FROM python:3.10

WORKDIR /app

# Install system dependencies needed for building packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with timeout and retries
RUN pip install --no-cache-dir --timeout=1000 -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p storage/images/original storage/images/preprocessed

# Expose port
EXPOSE 8000

# Run the application - Railway sets PORT env variable
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
