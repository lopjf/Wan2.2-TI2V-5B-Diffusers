# Use RunPod's PyTorch base image with CUDA support
FROM runpod/pytorch:2.1.0-py3.10-cuda12.1.0-devel-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model to speed up cold starts
RUN python -c "from huggingface_hub import snapshot_download; \
    snapshot_download('Wan-AI/Wan2.2-TI2V-5B-Diffusers', \
    local_dir='/app/model_cache', \
    token=None)"

# Set HuggingFace cache to the pre-downloaded location
ENV HF_HOME=/app/model_cache
ENV TRANSFORMERS_CACHE=/app/model_cache
ENV HF_DATASETS_CACHE=/app/model_cache

# Copy handler
COPY handler.py .

# Set the entrypoint
CMD ["python", "-u", "handler.py"]
