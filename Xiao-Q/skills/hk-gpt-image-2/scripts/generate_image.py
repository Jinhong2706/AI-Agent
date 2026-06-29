#!/usr/bin/env python3
"""
GPT-Image-2 Image Generation Script
Supports text-to-image and image-to-image via OpenAI-HK API
"""

import argparse
import json
import os
import random
import time
import urllib.request
import urllib.error
import mimetypes

API_BASE = "https://api.openai-hk.com"

def save_image_from_url(url: str, output_path: str) -> bool:
    """Download image from URL and save to file."""
    try:
        urllib.request.urlretrieve(url, output_path)
        return True
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False

def text_to_image(api_key: str, prompt: str, model: str = "gpt-image-2",
                  size: str = "1024x1024", quality: str = "low", n: int = 1,
                  output: str = None, response_format: str = "url") -> str:
    """Generate image from text prompt."""
    url = f"{API_BASE}/v1/images/generations"
    
    data = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
        "quality": quality,
        "response_format": response_format
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            "Authorization": f"Bearer hk-{api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        if "data" not in result or len(result["data"]) == 0:
            print("Error: No image data returned")
            return None
        
        image_data = result["data"][0]
        
        # Check for b64_json first, then url
        if "b64_json" in image_data and image_data["b64_json"]:
            import base64
            img_data = base64.b64decode(image_data["b64_json"])
            if output:
                with open(output, "wb") as f:
                    f.write(img_data)
                print(f"Image saved to: {output}")
                return output
        
        image_url = image_data.get("url")
        if not image_url:
            print("Error: No URL in response")
            return None
        
        if output:
            if save_image_from_url(image_url, output):
                print(f"Image saved to: {output}")
                return output
        else:
            print(f"Image URL: {image_url}")
            return image_url
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ""
        print(f"HTTP Error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def image_to_image(api_key: str, prompt: str, input_images: list,
                   model: str = "gpt-image-2", n: int = 1,
                   output: str = None) -> str:
    """Generate image from reference image(s) - image editing."""
    url = f"{API_BASE}/v1/images/edits"
    
    boundary = f"----FormBoundary{random.randint(1000000000000, 9999999999999)}"
    
    body = b""
    
    # Add model
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="model"\r\n\r\n'
    body += f"{model}\r\n".encode()
    
    # Add prompt
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="prompt"\r\n\r\n'
    body += f"{prompt}\r\n".encode()
    
    # Add quality
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="quality"\r\n\r\n'
    body += b"low\r\n"
    
    # Add images
    for img_path in input_images:
        if not os.path.exists(img_path):
            print(f"Error: File not found: {img_path}")
            continue
        
        mime_type = mimetypes.guess_type(img_path)[0] or "image/png"
        filename = os.path.basename(img_path)
        
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="image[]"; filename="{filename}"\r\n'.encode()
        body += f"Content-Type: {mime_type}\r\n\r\n".encode()
        
        with open(img_path, "rb") as f:
            body += f.read() + b"\r\n"
    
    body += f"--{boundary}--\r\n".encode()
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer hk-{api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        if "data" not in result or len(result["data"]) == 0:
            print("Error: No image data returned")
            return None
        
        image_url = result["data"][0].get("url")
        if not image_url:
            print("Error: No URL in response")
            return None
        
        if output:
            if save_image_from_url(image_url, output):
                print(f"Image saved to: {output}")
                return output
        else:
            print(f"Image URL: {image_url}")
            return image_url
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ""
        print(f"HTTP Error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="GPT-Image-2 Image Generation")
    parser.add_argument("--api-key", required=True, help="OpenAI-HK API key (hk-xxx)")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--model", default="gpt-image-2",
                        choices=["gpt-image-2", "gpt-image-1.5", "gpt-image-1"],
                        help="Model to use")
    parser.add_argument("--size", default="1024x1024",
                        help="Output size (e.g., 1024x1024, 1280x720, 720x1280)")
    parser.add_argument("--quality", default="low",
                        choices=["low", "medium", "high", "auto"],
                        help="Quality (low/medium/high/auto)")
    parser.add_argument("--input-image", help="Reference image path for image-to-image")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--n", type=int, default=1, help="Number of images to generate")
    
    args = parser.parse_args()
    
    # Generate output filename if not provided
    if not args.output:
        random_num = random.randint(100000, 999999)
        date_str = time.strftime("%Y-%m-%d")
        ext = "png"
        output_dir = "/root/.openclaw/media/images"
        os.makedirs(output_dir, exist_ok=True)
        args.output = f"{output_dir}/{date_str}-{random_num}.{ext}"
    
    if args.input_image:
        # Image-to-image
        result = image_to_image(
            api_key=args.api_key,
            prompt=args.prompt,
            input_images=[args.input_image],
            model=args.model,
            n=args.n,
            output=args.output
        )
    else:
        # Text-to-image
        result = text_to_image(
            api_key=args.api_key,
            prompt=args.prompt,
            model=args.model,
            size=args.size,
            quality=args.quality,
            n=args.n,
            output=args.output
        )
    
    if result:
        print(f"Success: {result}")
        return 0
    else:
        print("Failed to generate image")
        return 1

if __name__ == "__main__":
    exit(main())