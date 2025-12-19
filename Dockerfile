# Use official PyTorch image with CUDA 12.1 support
FROM pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime

# Set working directory
WORKDIR /app

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set HuggingFace cache directory (model will download on first run)
ENV HF_HOME=/workspace/model_cache
ENV TRANSFORMERS_CACHE=/workspace/model_cache
ENV HF_DATASETS_CACHE=/workspace/model_cache
ENV HF_HUB_ENABLE_HF_TRANSFER=1

# Copy handler
COPY handler.py .

# Set the entrypoint
CMD ["python", "-u", "handler.py"]
