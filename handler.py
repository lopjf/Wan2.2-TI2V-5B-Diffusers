"""
RunPod Serverless Handler for Wan2.2-TI2V-5B-Diffusers
Image-to-Video Generation Endpoint
"""

import os
import sys
import base64
import torch
import runpod
from diffusers import WanPipeline, AutoencoderKLWan
from PIL import Image
import requests
from io import BytesIO
import tempfile
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Global pipeline variable for model caching
pipeline = None


def download_image(url: str) -> Image.Image:
    """Download image from URL and return PIL Image"""
    try:
        logger.info(f"Downloading image from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        logger.info(f"Image downloaded successfully. Size: {image.size}, Mode: {image.mode}")
        return image.convert("RGB")
    except Exception as e:
        logger.error(f"Failed to download image: {str(e)}")
        raise


def load_pipeline():
    """Load the Wan pipeline with VAE"""
    global pipeline

    if pipeline is not None:
        logger.info("Using cached pipeline")
        return pipeline

    logger.info("="*50)
    logger.info("Loading Wan2.2-TI2V-5B-Diffusers pipeline...")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
        logger.info(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    logger.info("="*50)

    model_id = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"

    try:
        # Load VAE in float32 for better quality
        logger.info("Loading VAE...")
        vae = AutoencoderKLWan.from_pretrained(
            model_id,
            subfolder="vae",
            torch_dtype=torch.float32
        )
        logger.info("✓ VAE loaded successfully")

        # Load pipeline in bfloat16 for efficiency
        logger.info("Loading main pipeline...")
        pipeline = WanPipeline.from_pretrained(
            model_id,
            vae=vae,
            torch_dtype=torch.bfloat16
        )
        logger.info("✓ Pipeline loaded successfully")

        # Move to GPU
        logger.info("Moving pipeline to GPU...")
        pipeline.to("cuda")
        logger.info("✓ Pipeline ready on GPU")
        logger.info("="*50)

        return pipeline
    except Exception as e:
        logger.error(f"Failed to load pipeline: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def generate_video(job):
    """
    Generate video from image using Wan pipeline

    Expected input format:
    {
        "prompt": str,
        "negative_prompt": str (optional),
        "image_url": str,
        "seed": int (optional),
        "cfg": float (optional, default 5.0),
        "width": int (optional, default 1280),
        "height": int (optional, default 704),
        "length": int (optional, default 121 frames),
        "steps": int (optional, default 50)
    }
    """
    try:
        job_input = job["input"]

        # Extract parameters with defaults
        prompt = job_input.get("prompt", "")
        negative_prompt = job_input.get("negative_prompt", "")
        image_url = job_input.get("image_url")
        seed = job_input.get("seed", 42)
        guidance_scale = job_input.get("cfg", 5.0)
        width = job_input.get("width", 1280)
        height = job_input.get("height", 704)
        num_frames = job_input.get("length", 121)
        num_inference_steps = job_input.get("steps", 50)

        logger.info(f"Generation parameters: prompt='{prompt[:50]}...', size={width}x{height}, "
                   f"frames={num_frames}, steps={num_inference_steps}, cfg={guidance_scale}")

        # Validate required parameters
        if not image_url:
            raise ValueError("image_url is required")

        # Download input image
        input_image = download_image(image_url)

        # Load pipeline
        pipe = load_pipeline()

        # Set seed for reproducibility
        if seed is not None:
            generator = torch.Generator(device="cuda").manual_seed(seed)
        else:
            generator = None

        # Generate video
        logger.info("Starting video generation...")
        output = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            image=input_image,
            height=height,
            width=width,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator,
        )

        logger.info("Video generation completed")

        # Export video to temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            output_path = tmp_file.name

        # Export frames to video at 24fps
        from diffusers.utils import export_to_video
        export_to_video(output.frames[0], output_path, fps=24)
        logger.info(f"Video exported to {output_path}")

        # Read video file and encode to base64
        with open(output_path, "rb") as video_file:
            video_bytes = video_file.read()
            video_base64 = base64.b64encode(video_bytes).decode("utf-8")

        # Clean up temporary file
        os.unlink(output_path)
        logger.info("Temporary file cleaned up")

        # Return in the expected format
        return {
            "video": video_base64
        }

    except Exception as e:
        logger.error(f"Error during video generation: {str(e)}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("RunPod Serverless Handler for Wan2.2-TI2V-5B Starting...")
    logger.info("="*60)
    logger.info(f"Python version: {sys.version}")
    logger.info(f"PyTorch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"CUDA version: {torch.version.cuda}")
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"HF_HOME: {os.getenv('HF_HOME', 'not set')}")
    logger.info("="*60)
    logger.info("Handler ready - waiting for jobs...")
    logger.info("="*60)

    runpod.serverless.start({"handler": generate_video})
