# Troubleshooting Guide

## Workers Stuck in "Initializing" Status

### Problem
Workers show "Initializing" status for extended periods (hours/days) and never become ready.

### Root Cause
This typically means the Docker container is failing to build or start properly.

### Solution

#### 1. Check Build Logs (RunPod Console)

1. Go to your endpoint in RunPod console
2. Click on "Logs" tab
3. Look for build errors or timeouts

Common errors to look for:
- `Failed to download model`
- `Timeout exceeded`
- `CUDA not available`
- `Import errors`

#### 2. Verify Dockerfile Changes

Make sure your Dockerfile does NOT pre-download the model during build:

**Bad (causes timeout):**
```dockerfile
RUN python -c "from huggingface_hub import snapshot_download; \
    snapshot_download('Wan-AI/Wan2.2-TI2V-5B-Diffusers', ...)"
```

**Good (downloads on first run):**
```dockerfile
# Set HuggingFace cache directory (model will download on first run)
ENV HF_HOME=/workspace/model_cache
```

#### 3. Test Build Locally

```bash
# Build the image locally to catch errors
docker build -t wan-i2v-test .

# If successful, run it
docker run --gpus all wan-i2v-test
```

#### 4. Redeploy with Fixed Dockerfile

After fixing the Dockerfile:

**For GitHub deployments:**
```bash
git add Dockerfile handler.py requirements.txt
git commit -m "Fix: Remove model pre-download from Dockerfile"
git push
```

Then in RunPod:
1. Go to your endpoint
2. Click "Edit"
3. Click "Rebuild" or "Force Redeploy"
4. Wait for new build (should take 5-10 minutes, not hours)

**For Docker Hub deployments:**
```bash
docker build -t YOUR_USERNAME/wan-i2v:latest .
docker push YOUR_USERNAME/wan-i2v:latest
# Then rebuild endpoint in RunPod
```

#### 5. Monitor Startup Logs

Once redeployed, check logs for:
```
RunPod Serverless Handler for Wan2.2-TI2V-5B Starting...
Python version: ...
PyTorch version: ...
CUDA available: True
Handler ready - waiting for jobs...
```

If you see these logs, the container started successfully!

---

## First Request Takes Very Long

### Problem
First video generation request takes 5-10 minutes or times out.

### Root Cause
Model is being downloaded on first run (~20GB download).

### Solution

#### Expected Behavior
- **First request**: 5-10 minutes (model download + generation)
- **Subsequent requests**: 30-90 seconds (generation only)

#### Speed Up First Request

1. **Use faster network endpoint** - Some RunPod regions have faster download speeds
2. **Keep workers warm** - Set `min_workers: 1` to avoid cold starts (costs more)
3. **Pre-warm with test request** - After deployment, send a test request and wait

#### Monitor Download Progress

Check logs during first request:
```
Loading Wan2.2-TI2V-5B-Diffusers pipeline...
Loading VAE...
✓ VAE loaded successfully
Loading main pipeline...
```

---

## CUDA Out of Memory Errors

### Problem
```
RuntimeError: CUDA out of memory
```

### Solution

#### 1. Use GPU with More VRAM
- **Minimum**: RTX 4090 (24GB)
- **Recommended**: A6000 (48GB) or A40 (48GB)

#### 2. Reduce Video Parameters
In your request, use:
```json
{
  "width": 512,      // Instead of 1280
  "height": 896,     // Instead of 704
  "length": 81,      // Instead of 121 (shorter video)
  "steps": 30        // Instead of 50
}
```

#### 3. Clear GPU Memory Between Runs
The handler already does this, but if you're testing locally:
```python
torch.cuda.empty_cache()
```

---

## Job Status Stuck in "IN_QUEUE" or "IN_PROGRESS"

### Problem
Job never completes, stuck in processing state.

### Possible Causes

#### 1. No Workers Available
**Check**: RunPod console → Endpoint → Workers tab
**Solution**: Increase `max_workers` or wait for worker to become available

#### 2. Worker Crashed
**Check**: Logs for error messages
**Solution**: Review error logs and fix code issues

#### 3. Request Timeout
**Check**: Job execution time in logs
**Solution**: Increase "Max Response Time" in endpoint settings:
1. Go to endpoint settings
2. Set "Max Response Time" to `600` seconds (10 min) or higher
3. Save changes

---

## Import Errors or Missing Dependencies

### Problem
```
ModuleNotFoundError: No module named 'diffusers'
ImportError: cannot import name 'WanPipeline'
```

### Solution

#### 1. Verify requirements.txt
Ensure you have the latest diffusers:
```
git+https://github.com/huggingface/diffusers
```

#### 2. Rebuild Container
```bash
# For Docker deployments
docker build --no-cache -t YOUR_USERNAME/wan-i2v:latest .

# For GitHub deployments
git push  # RunPod will rebuild automatically
```

#### 3. Check Diffusers Version
In handler logs, you should see:
```
✓ Pipeline loaded successfully
```

---

## Video Generation Produces Poor Quality

### Problem
Generated videos are blurry, distorted, or don't follow the prompt.

### Solution

#### 1. Increase Inference Steps
```json
{
  "steps": 50  // Or higher (up to 100)
}
```

More steps = better quality but slower generation.

#### 2. Adjust Guidance Scale
```json
{
  "cfg": 5.0  // Try values between 3.0 and 7.0
}
```

- Lower (3.0): More creative, less prompt adherence
- Higher (7.0): Stricter prompt adherence

#### 3. Improve Prompt
Add motion and FPS hints:
```
"A cat walking in a garden, smooth motion, 24 fps, high quality"
```

#### 4. Use Better Negative Prompt
```
"flicker, distortion, glitch, warped perspective, slow motion, blur, low quality"
```

---

## Base64 Decoding Fails

### Problem
```
Error: Invalid base64 string
```

### Solution

#### 1. Check Response Format
Response should be:
```json
{
  "output": {
    "video": "AAAAHGZ0eXBpc..."
  }
}
```

#### 2. Handle Response Correctly

**Python:**
```python
import base64

video_b64 = result["output"]["video"]
video_bytes = base64.b64decode(video_b64)
with open("output.mp4", "wb") as f:
    f.write(video_bytes)
```

**n8n (already handled):**
The Convert Base64 to Video node handles this automatically.

---

## Network Timeout During Deployment

### Problem
```
Error: Failed to pull image
Error: Timeout during build
```

### Solution

#### 1. Check Image Size
Ensure your Docker image isn't too large (should be <10GB without model).

#### 2. Use Docker Hub with Pre-built Image
Instead of GitHub auto-build:
```bash
docker build -t YOUR_USERNAME/wan-i2v:latest .
docker push YOUR_USERNAME/wan-i2v:latest
```

Then deploy using the Docker Hub URL directly.

#### 3. Verify GitHub Repository Access
If using GitHub deployment, ensure:
- Repository is public, OR
- RunPod has access to your private repository

---

## How to View Detailed Logs

### RunPod Console
1. Go to your endpoint
2. Click "Logs" tab
3. Select worker ID
4. View real-time logs

### Using RunPod CLI
```bash
runpodctl logs --endpoint YOUR_ENDPOINT_ID
```

### Log Level Control
Set in handler.py:
```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
```

---

## Cost Optimization Tips

### Problem
RunPod costs are higher than expected.

### Solutions

1. **Scale to Zero**: Set `min_workers: 0` when not in use
2. **Use Cheaper GPUs**: RTX 4090 < A6000 < A40 in cost
3. **Reduce Steps**: Use `steps: 30` instead of `50` for faster/cheaper generation
4. **Shorter Videos**: Reduce `length` parameter
5. **Batch Processing**: Process multiple videos in sequence to amortize cold start

---

## Getting More Help

### Check Logs First
Always review logs before seeking help. Most issues show clear error messages.

### Resources
- **RunPod Discord**: https://discord.gg/runpod
- **HuggingFace Model**: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers
- **Diffusers Docs**: https://huggingface.co/docs/diffusers

### When Reporting Issues
Include:
1. Full error message from logs
2. Input parameters used
3. GPU type
4. Deployment method (GitHub/Docker)
5. Worker status and uptime
