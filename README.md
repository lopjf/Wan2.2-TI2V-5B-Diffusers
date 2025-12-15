# RunPod Serverless: Wan2.2-TI2V-5B Image-to-Video

A lightweight RunPod serverless endpoint for generating videos from images using the [Wan2.2-TI2V-5B-Diffusers](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers) model.

## Features

- Image-to-Video generation at 720P resolution (24fps)
- Compatible with existing VideoGeneratorAI.json workflow
- Optimized for consumer GPUs (RTX 4090 and above recommended)
- Pre-cached model for faster cold starts
- Base64 video output for easy integration

## Quick Start

### 1. Deploy to RunPod

#### Option A: Deploy from GitHub (Recommended)

1. Push this repository to GitHub
2. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
3. Click "New Endpoint"
4. Select "Deploy from GitHub"
5. Enter your repository URL
6. Configure:
   - **Min Workers**: 0 (for cost savings)
   - **Max Workers**: 3
   - **GPU Type**: RTX 4090 or A6000
   - **Container Disk**: 20GB minimum
7. Deploy and note your endpoint ID

#### Option B: Deploy from Docker Hub

1. Build and push the Docker image:
```bash
cd runpod-wan-i2v
docker build -t your-dockerhub-username/wan-i2v:latest .
docker push your-dockerhub-username/wan-i2v:latest
```

2. Deploy on RunPod using the Docker image URL

### 2. Test the Endpoint

Use the following request format:

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "A beautiful sunset over the ocean, 24 fps",
      "negative_prompt": "flicker, distortion, glitch, warped perspective, slow motion",
      "image_url": "https://example.com/your-image.jpg",
      "seed": 42,
      "cfg": 5.0,
      "width": 1280,
      "height": 704,
      "length": 121,
      "steps": 50
    }
  }'
```

### 3. Check Job Status

```bash
curl https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/status/JOB_ID \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY"
```

## API Reference

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | - | Text description for video generation |
| `negative_prompt` | string | No | "" | What to avoid in the generation |
| `image_url` | string | Yes | - | URL of the input image |
| `seed` | integer | No | 42 | Random seed for reproducibility |
| `cfg` | float | No | 5.0 | Guidance scale (higher = more prompt adherence) |
| `width` | integer | No | 1280 | Video width (720P: 1280x704 or 704x1280) |
| `height` | integer | No | 704 | Video height |
| `length` | integer | No | 121 | Number of frames (~5 seconds at 24fps) |
| `steps` | integer | No | 50 | Number of inference steps (higher = better quality, slower) |

### Output Format

```json
{
  "id": "job-id",
  "status": "COMPLETED",
  "output": {
    "video": "base64_encoded_video_data..."
  }
}
```

## Integration with VideoGeneratorAI.json

This endpoint is fully compatible with your existing n8n workflow. Simply update the endpoint URL in the "Submit Video Generation Job" node:

```
https://api.runpod.ai/v2/YOUR_NEW_ENDPOINT_ID/run
```

The input/output format matches exactly, so no other changes are needed!

## Performance & Costs

### GPU Requirements
- **Minimum**: RTX 4090 (24GB VRAM)
- **Recommended**: A6000 (48GB VRAM) for better performance
- **Budget**: A40 (48GB VRAM)

### Generation Times (Approximate)
- RTX 4090: ~30-60 seconds per video (50 steps)
- A6000: ~25-45 seconds per video (50 steps)

### Cost Optimization Tips
1. Set `min_workers: 0` to avoid idle costs
2. Use lower `steps` (30-40) for faster/cheaper generation
3. Reduce `length` for shorter videos
4. Enable auto-scaling based on queue size

## Troubleshooting

### Cold Start Times
First request after idle may take 2-3 minutes to load the model. Subsequent requests are much faster.

### Out of Memory
- Reduce `width` and `height`
- Reduce `length` (number of frames)
- Use a GPU with more VRAM

### Image Download Fails
- Ensure `image_url` is publicly accessible
- Check that the URL returns a valid image format (JPG, PNG)

### Video Quality Issues
- Increase `steps` (50-100) for better quality
- Adjust `cfg` (3.0-7.0) for prompt adherence
- Try different `seed` values

## Local Development

### Prerequisites
- NVIDIA GPU with 24GB+ VRAM
- CUDA 12.1+
- Python 3.10+

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally (requires runpod CLI setup)
python handler.py
```

## Model Information

- **Model**: Wan-AI/Wan2.2-TI2V-5B-Diffusers
- **Type**: Image-to-Video (I2V)
- **Resolution**: 720P (1280×704 or 704×1280)
- **Frame Rate**: 24 fps
- **Max Frames**: 121 (5 seconds)
- **License**: Check model card on HuggingFace

## Support

For issues related to:
- **Deployment**: Check RunPod documentation
- **Model**: Visit [Wan-AI/Wan2.2-TI2V-5B-Diffusers](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers)
- **This repo**: Open an issue on GitHub

## License

This wrapper code is provided as-is. Please refer to the Wan2.2-TI2V-5B-Diffusers model license for usage restrictions.
