#!/bin/bash

# Example request script for testing the RunPod endpoint
# Usage: ./example_request.sh

# Configuration - Update these values
RUNPOD_API_KEY="${RUNPOD_API_KEY:-YOUR_API_KEY_HERE}"
ENDPOINT_ID="${ENDPOINT_ID:-YOUR_ENDPOINT_ID_HERE}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Validate configuration
if [ "$RUNPOD_API_KEY" = "YOUR_API_KEY_HERE" ] || [ "$ENDPOINT_ID" = "YOUR_ENDPOINT_ID_HERE" ]; then
    echo -e "${RED}Error: Please set RUNPOD_API_KEY and ENDPOINT_ID environment variables${NC}"
    echo ""
    echo "Usage:"
    echo "  export RUNPOD_API_KEY='your-api-key'"
    echo "  export ENDPOINT_ID='your-endpoint-id'"
    echo "  ./example_request.sh"
    exit 1
fi

echo -e "${GREEN}Submitting video generation job...${NC}"
echo "Endpoint: https://api.runpod.ai/v2/${ENDPOINT_ID}/run"
echo ""

# Submit job
RESPONSE=$(curl -s -X POST "https://api.runpod.ai/v2/${ENDPOINT_ID}/run" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "A beautiful sunset over the ocean, gentle waves, 24 fps",
      "negative_prompt": "flicker, distortion, glitch, warped perspective, slow motion",
      "image_url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/cat.png",
      "seed": 42,
      "cfg": 5.0,
      "width": 704,
      "height": 1280,
      "length": 121,
      "steps": 30
    }
  }')

# Extract job ID
JOB_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
    echo -e "${RED}Failed to submit job${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

echo -e "${GREEN}Job submitted successfully!${NC}"
echo "Job ID: $JOB_ID"
echo ""
echo -e "${YELLOW}Waiting for completion...${NC}"
echo "(This may take 30-120 seconds depending on GPU availability and cold start)"
echo ""

# Poll for status
STATUS="IN_QUEUE"
COUNTER=0
MAX_ATTEMPTS=120  # 10 minutes

while [ "$STATUS" != "COMPLETED" ] && [ "$STATUS" != "FAILED" ] && [ "$STATUS" != "CANCELLED" ]; do
    sleep 5
    COUNTER=$((COUNTER + 1))

    if [ $COUNTER -gt $MAX_ATTEMPTS ]; then
        echo -e "${RED}Timeout: Job did not complete within 10 minutes${NC}"
        exit 1
    fi

    STATUS_RESPONSE=$(curl -s "https://api.runpod.ai/v2/${ENDPOINT_ID}/status/${JOB_ID}" \
      -H "Authorization: Bearer ${RUNPOD_API_KEY}")

    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*' | cut -d'"' -f4)

    echo -e "${YELLOW}[$(date +%H:%M:%S)] Status: ${STATUS}${NC}"

    if [ "$STATUS" = "FAILED" ]; then
        echo -e "${RED}Job failed!${NC}"
        echo "Response: $STATUS_RESPONSE"
        exit 1
    fi

    if [ "$STATUS" = "CANCELLED" ]; then
        echo -e "${RED}Job was cancelled${NC}"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}✓ Job completed successfully!${NC}"
echo ""
echo "To view the full response with video data:"
echo "curl -s \"https://api.runpod.ai/v2/${ENDPOINT_ID}/status/${JOB_ID}\" \\"
echo "  -H \"Authorization: Bearer ${RUNPOD_API_KEY}\""
echo ""
echo -e "${YELLOW}Note: The video is base64 encoded in the 'output.video' field${NC}"
