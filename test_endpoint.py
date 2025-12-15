"""
Test script for the RunPod Wan I2V endpoint
"""

import requests
import json
import time
import base64
import sys
import os

# Configuration - Update these values
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "YOUR_API_KEY_HERE")
ENDPOINT_ID = os.getenv("ENDPOINT_ID", "YOUR_ENDPOINT_ID_HERE")

# Test image URL - replace with your own
TEST_IMAGE_URL = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/cat.png"


def submit_job(endpoint_id, api_key, test_params=None):
    """Submit a video generation job"""

    if test_params is None:
        test_params = {
            "input": {
                "prompt": "A cat walking in a garden, smooth motion, 24 fps",
                "negative_prompt": "flicker, distortion, glitch, warped perspective",
                "image_url": TEST_IMAGE_URL,
                "seed": 42,
                "cfg": 5.0,
                "width": 704,
                "height": 1280,
                "length": 121,
                "steps": 30  # Using fewer steps for faster testing
            }
        }

    url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("Submitting job...")
    print(f"Endpoint: {url}")
    print(f"Parameters: {json.dumps(test_params, indent=2)}")

    response = requests.post(url, headers=headers, json=test_params)
    response.raise_for_status()

    result = response.json()
    job_id = result.get("id")

    print(f"\nJob submitted successfully!")
    print(f"Job ID: {job_id}")

    return job_id


def check_status(endpoint_id, api_key, job_id):
    """Check the status of a job"""
    url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def wait_for_completion(endpoint_id, api_key, job_id, timeout=600):
    """Wait for job to complete"""
    start_time = time.time()

    print("\nWaiting for job to complete...")

    while True:
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Job did not complete within {timeout} seconds")

        status_result = check_status(endpoint_id, api_key, job_id)
        status = status_result.get("status")

        print(f"Status: {status}")

        if status == "COMPLETED":
            print("\nJob completed successfully!")
            return status_result
        elif status == "FAILED":
            error = status_result.get("error", "Unknown error")
            raise RuntimeError(f"Job failed: {error}")
        elif status == "CANCELLED":
            raise RuntimeError("Job was cancelled")

        # Wait before checking again
        time.sleep(10)


def save_video(base64_data, output_path="output_video.mp4"):
    """Save base64 video data to file"""
    video_bytes = base64.b64decode(base64_data)

    with open(output_path, "wb") as f:
        f.write(video_bytes)

    print(f"\nVideo saved to: {output_path}")
    print(f"File size: {len(video_bytes) / 1024 / 1024:.2f} MB")


def main():
    """Main test function"""

    # Validate configuration
    if RUNPOD_API_KEY == "YOUR_API_KEY_HERE" or ENDPOINT_ID == "YOUR_ENDPOINT_ID_HERE":
        print("Error: Please set RUNPOD_API_KEY and ENDPOINT_ID environment variables or update the script")
        print("\nUsage:")
        print("  export RUNPOD_API_KEY='your-api-key'")
        print("  export ENDPOINT_ID='your-endpoint-id'")
        print("  python test_endpoint.py")
        sys.exit(1)

    try:
        # Submit job
        job_id = submit_job(ENDPOINT_ID, RUNPOD_API_KEY)

        # Wait for completion
        result = wait_for_completion(ENDPOINT_ID, RUNPOD_API_KEY, job_id)

        # Extract and save video
        video_base64 = result.get("output", {}).get("video")

        if video_base64:
            save_video(video_base64)
            print("\nTest completed successfully!")
        else:
            print("\nWarning: No video data in output")
            print(f"Full result: {json.dumps(result, indent=2)}")

    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
