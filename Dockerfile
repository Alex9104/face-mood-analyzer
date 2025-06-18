# Build stage
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 as builder

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Install only the required packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Final stage
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

# Install only the necessary system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the necessary files from the builder stage
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads/reference uploads/photos output/marked_photos output/videos

EXPOSE 5000

# Command to run the application
CMD ["python3", "app.py"] 