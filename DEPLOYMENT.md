# Deployment Guide

This guide walks you through deploying the Wan I2V endpoint to RunPod.

## Prerequisites

1. RunPod account (sign up at https://runpod.io)
2. GitHub account (for deployment from repository)
3. Basic knowledge of Docker (if building custom images)

## Method 1: Deploy Directly from GitHub (Easiest)

This is the recommended method as it's the simplest and doesn't require building Docker images locally.

### Step 1: Push to GitHub

```bash
cd runpod-wan-i2v
git init
git add .
git commit -m "Initial commit: Wan I2V serverless endpoint"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/runpod-wan-i2v.git
git push -u origin main
```

### Step 2: Deploy on RunPod

1. Go to https://www.runpod.io/console/serverless
2. Click **"+ New Endpoint"**
3. Select **"Deploy from GitHub"**
4. Authorize RunPod to access your GitHub repositories
5. Select your repository: `YOUR_USERNAME/runpod-wan-i2v`
6. Configure the endpoint:
   - **Name**: `wan-i2v-prod` (or any name you prefer)
   - **GPU Types**: Select `NVIDIA RTX 4090`, `NVIDIA A6000`, or `NVIDIA A40`
   - **Min Workers**: `0` (recommended for cost savings)
   - **Max Workers**: `3` (adjust based on your expected load)
   - **Idle Timeout**: `300` seconds (5 minutes)
   - **Container Disk**: `20 GB` minimum
   - **Max Response Time**: `600` seconds (10 minutes for long videos)
7. Click **"Deploy"**

### Step 3: Note Your Endpoint Details

After deployment, you'll receive:
- **Endpoint ID**: Something like `qiei69e92eqzfk`
- **API URL**: `https://api.runpod.ai/v2/YOUR_ENDPOINT_ID`

Save these for later use!

## Method 2: Deploy from Docker Hub

If you want more control over the Docker image, you can build and push it yourself.

### Step 1: Build the Docker Image

```bash
cd runpod-wan-i2v
docker build -t YOUR_DOCKERHUB_USERNAME/wan-i2v:latest .
```

Note: Building will take 15-30 minutes as it downloads the model.

### Step 2: Push to Docker Hub

```bash
docker login
docker push YOUR_DOCKERHUB_USERNAME/wan-i2v:latest
```

### Step 3: Deploy on RunPod

1. Go to https://www.runpod.io/console/serverless
2. Click **"+ New Endpoint"**
3. Select **"Deploy Custom Image"**
4. Enter your Docker image: `YOUR_DOCKERHUB_USERNAME/wan-i2v:latest`
5. Configure as described in Method 1, Step 2
6. Click **"Deploy"**

## Method 3: Using RunPod CLI (Advanced)

### Step 1: Install RunPod CLI

```bash
pip install runpodctl
```

### Step 2: Configure CLI

```bash
runpodctl config set-api-key YOUR_RUNPOD_API_KEY
```

### Step 3: Deploy

```bash
# Update runpod.yaml with your Docker image
runpodctl project deploy
```

## Post-Deployment Setup

### 1. Get Your API Key

1. Go to https://www.runpod.io/console/user/settings
2. Navigate to **"API Keys"**
3. Click **"+ Create API Key"**
4. Name it (e.g., "Wan I2V Production")
5. Copy and save the key securely

### 2. Test the Endpoint

```bash
# Set environment variables
export RUNPOD_API_KEY="your-api-key-here"
export ENDPOINT_ID="your-endpoint-id-here"

# Run test script
python test_endpoint.py
```

### 3. Update Your n8n Workflow

In VideoGeneratorAI.json, update the "Submit Video Generation Job" node:

1. Open the n8n workflow
2. Find the **"Submit Video Generation Job"** HTTP Request node
3. Update the URL to:
   ```
   https://api.runpod.ai/v2/YOUR_NEW_ENDPOINT_ID/run
   ```
4. Update the authentication header with your new RunPod API key
5. Save and test the workflow

## Monitoring & Optimization

### View Logs

1. Go to your endpoint in the RunPod console
2. Click on **"Logs"** tab
3. View real-time logs from your workers

### Monitor Performance

Check the **"Analytics"** tab to see:
- Request count
- Average execution time
- Error rate
- GPU utilization

### Cost Optimization

1. **Use min_workers: 0**: Only pay when processing jobs
2. **Reduce steps**: 30-40 steps instead of 50 for faster generation
3. **Shorter videos**: Reduce `length` parameter
4. **GPU selection**: RTX 4090 is cheaper than A6000

### Scaling Tips

- Set `max_workers` based on expected concurrent requests
- Monitor queue depth and adjust accordingly
- Use higher-end GPUs (A6000) for better throughput if cost allows

## Troubleshooting

### Deployment Fails

**Error**: "Failed to pull image"
- **Solution**: Ensure your Docker image is public or RunPod has access
- Check the image tag is correct

**Error**: "Container exits immediately"
- **Solution**: Check logs for Python errors
- Verify all dependencies are in requirements.txt

### Cold Starts Too Slow

**Problem**: First request takes 3+ minutes

**Solutions**:
1. Pre-download model in Dockerfile (already done)
2. Set `min_workers: 1` to keep one worker warm (costs more)
3. Use RunPod's "keep warm" feature

### Out of Memory

**Error**: CUDA out of memory

**Solutions**:
1. Use GPU with more VRAM (A6000/A40 with 48GB)
2. Reduce video resolution in default parameters
3. Reduce `num_frames`

### Jobs Timing Out

**Error**: Job exceeds max timeout

**Solutions**:
1. Increase "Max Response Time" in endpoint settings
2. Reduce `steps` parameter
3. Use faster GPU

## Updating Your Deployment

### GitHub Method

```bash
# Make your changes
git add .
git commit -m "Update: description of changes"
git push

# RunPod will automatically rebuild and redeploy
```

### Docker Hub Method

```bash
# Rebuild image
docker build -t YOUR_DOCKERHUB_USERNAME/wan-i2v:latest .

# Push update
docker push YOUR_DOCKERHUB_USERNAME/wan-i2v:latest

# Restart endpoint in RunPod console
```

## Security Best Practices

1. **Never commit API keys**: Use environment variables
2. **Limit API key permissions**: Create separate keys for different environments
3. **Monitor usage**: Set up billing alerts
4. **Validate inputs**: The handler includes basic validation
5. **Rate limiting**: Consider implementing rate limits in your application

## Getting Help

- **RunPod Issues**: https://discord.gg/runpod
- **Model Issues**: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers/discussions
- **This Repository**: Open a GitHub issue

## Next Steps

1. ✅ Deploy the endpoint
2. ✅ Test with test_endpoint.py
3. ✅ Update your n8n workflow
4. 🎯 Monitor performance and costs
5. 🎯 Optimize parameters for your use case
6. 🎯 Scale as needed
