# Quick Fix: Workers Stuck Initializing

If your workers have been stuck in "Initializing" for 2+ days, follow these steps:

## The Problems

1. **Invalid Base Image**: The Docker base image `runpod/pytorch:2.1.0-py3.10-cuda12.1.0-devel-ubuntu22.04` doesn't exist
2. **Model Pre-download**: Dockerfile was trying to download the 20GB model during build, which times out

## The Fix

We've updated three files to fix this:

1. **Dockerfile** - Removed model pre-download
2. **handler.py** - Added better logging and error handling
3. **requirements.txt** - Added faster download library

## Steps to Deploy the Fix

### 1. Commit and Push Changes

```bash
cd /Users/loris/Documents/Wan2.2-TI2V-5B-Diffusers

# Check what changed
git status

# Add all changes
git add Dockerfile handler.py requirements.txt TROUBLESHOOTING.md QUICKFIX.md

# Commit
git commit -m "Fix: Remove model pre-download, add better logging"

# Push to GitHub
git push
```

### 2. Force Rebuild in RunPod

1. Go to https://www.runpod.io/console/serverless
2. Find your endpoint (the one stuck initializing)
3. Click on it
4. Click "Edit" button
5. Scroll down and click "Force Redeploy" or "Rebuild"
6. Wait 5-10 minutes for build to complete

**Important**: The build should complete in 5-10 minutes now, NOT hours!

### 3. Monitor Build Progress

1. Go to "Logs" tab in your endpoint
2. Watch for these messages:
   ```
   Building Docker image...
   Installing dependencies...
   Build complete!
   ```

3. Then watch for handler startup:
   ```
   RunPod Serverless Handler for Wan2.2-TI2V-5B Starting...
   Python version: 3.10.x
   PyTorch version: 2.x.x
   CUDA available: True
   Handler ready - waiting for jobs...
   ```

### 4. Test with First Request

Send a test request using the test script:

```bash
export RUNPOD_API_KEY="your-api-key"
export ENDPOINT_ID="your-endpoint-id"

python test_endpoint.py
```

**Expected behavior:**
- First request: 5-10 minutes (downloads model)
- Subsequent requests: 30-90 seconds

### 5. Update Your n8n Workflow

No changes needed! The API format is exactly the same.

---

## What Changed?

### 1. Fixed Base Image

**Before (BAD - image doesn't exist):**
```dockerfile
FROM runpod/pytorch:2.1.0-py3.10-cuda12.1.0-devel-ubuntu22.04
```

**After (GOOD - official PyTorch image):**
```dockerfile
FROM pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime
```

### 2. Removed Model Pre-download

**Before (BAD - causes timeout):**
```dockerfile
RUN python -c "from huggingface_hub import snapshot_download; \
    snapshot_download('Wan-AI/Wan2.2-TI2V-5B-Diffusers', ...)"
```

**After (GOOD - downloads on first run):**
```dockerfile
ENV HF_HOME=/workspace/model_cache
ENV HF_HUB_ENABLE_HF_TRANSFER=1  # Faster downloads
```

---

## Alternative: Start Fresh

If rebuild doesn't work, create a new endpoint:

1. Delete the old stuck endpoint
2. Create new endpoint with your updated GitHub repo
3. Configure same settings (GPU, workers, etc.)
4. Deploy
5. Update your n8n workflow with new endpoint ID

---

## Verification Checklist

- [ ] Code pushed to GitHub
- [ ] Endpoint rebuilt in RunPod
- [ ] Build completes in <10 minutes
- [ ] Logs show "Handler ready - waiting for jobs..."
- [ ] Workers show "Ready" status (not "Initializing")
- [ ] Test request succeeds (may take 5-10 min for first request)
- [ ] Subsequent requests take <2 minutes

---

## Still Having Issues?

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed debugging steps.

Or check RunPod logs for specific error messages:
1. Go to endpoint in console
2. Click "Logs" tab
3. Look for errors in red
4. Search for that error in TROUBLESHOOTING.md
