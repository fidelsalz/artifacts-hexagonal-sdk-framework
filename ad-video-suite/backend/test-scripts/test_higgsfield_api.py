#!/usr/bin/env python3
"""
test_higgsfield_api.py — Test Higgsfield REST API (not MCP).

Loads credentials from .env, then:
  1. Generates an image with soul/standard
  2. Polls job status until done
  3. Prints the result URL

Usage:
    python test_higgsfield_api.py
"""
import asyncio
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

API_KEY    = os.environ.get("HIGGSFIELD_API_KEY", "")
API_SECRET = os.environ.get("HIGGSFIELD_API_SECRET", "")
BASE_URL   = "https://platform.higgsfield.ai"

if not API_KEY or API_KEY == "your_api_key_here":
    sys.exit("ERROR: set HIGGSFIELD_API_KEY and HIGGSFIELD_API_SECRET in backend/.env first")

AUTH_HEADER = f"Key {API_KEY}:{API_SECRET}"
HEADERS = {
    "Authorization": AUTH_HEADER,
    "Content-Type":  "application/json",
    "Accept":        "application/json",
}


# ---------------------------------------------------------------------------
# 1. Generate image
# ---------------------------------------------------------------------------

async def generate_image(
    prompt: str,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
) -> dict:
    payload = {
        "prompt":       prompt,
        "aspect_ratio": aspect_ratio,
        "resolution":   resolution,
    }
    print(f"\n[generate] POST {BASE_URL}/higgsfield-ai/soul/standard")
    print(f"  prompt      : {prompt[:80]}")
    print(f"  aspect_ratio: {aspect_ratio}  resolution: {resolution}")

    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            f"{BASE_URL}/higgsfield-ai/soul/standard",
            headers=HEADERS,
            json=payload,
        )
    print(f"  status      : {r.status_code}")
    body = r.json()
    print(f"  response    : {body}")
    r.raise_for_status()
    return body


# ---------------------------------------------------------------------------
# 2. Poll job status
# ---------------------------------------------------------------------------

async def poll_job(job_id: str, interval: int = 5, max_wait: int = 300) -> dict:
    url = f"{BASE_URL}/higgsfield-ai/soul/standard/{job_id}"
    print(f"\n[poll] GET {url}")
    deadline = time.time() + max_wait
    async with httpx.AsyncClient(timeout=30) as c:
        while time.time() < deadline:
            r = await c.get(url, headers=HEADERS)
            body = r.json()
            status = body.get("status", "unknown")
            print(f"  [{time.strftime('%H:%M:%S')}] status={status}")
            if status in ("completed", "succeeded", "done", "failed", "error"):
                print(f"  final: {body}")
                return body
            await asyncio.sleep(interval)
    raise TimeoutError(f"Job {job_id} did not complete within {max_wait}s")


# ---------------------------------------------------------------------------
# 3. List available models (optional)
# ---------------------------------------------------------------------------

async def list_models() -> None:
    candidates = [
        "/higgsfield-ai/models",
        "/higgsfield-ai/soul/models",
        "/api/models",
    ]
    async with httpx.AsyncClient(timeout=15) as c:
        for path in candidates:
            r = await c.get(f"{BASE_URL}{path}", headers=HEADERS)
            print(f"\n[models] GET {path} → {r.status_code}")
            if r.status_code == 200:
                print(f"  {r.text[:400]}")
                return
            print(f"  {r.text[:120]}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

async def main():
    print("=" * 60)
    print("Higgsfield REST API probe")
    print(f"  base_url : {BASE_URL}")
    print(f"  api_key  : {API_KEY[:8]}...")
    print("=" * 60)

    # Optional: list models first
    await list_models()

    # Generate a test image
    prompt = (
        "A serene mountain landscape at sunset with vibrant "
        "orange and purple skies, cinematic quality"
    )
    result = await generate_image(prompt)

    # Extract job_id — field name may vary by API version
    job_id = (
        result.get("job_id")
        or result.get("id")
        or result.get("generation_id")
        or result.get("task_id")
    )

    if not job_id:
        print("\n[warn] No job_id in response — generation may be synchronous.")
        print(f"Full response: {result}")
        return

    print(f"\n[ok] job_id = {job_id}")
    final = await poll_job(job_id)

    output_url = (
        final.get("output_url")
        or final.get("url")
        or final.get("image_url")
        or final.get("result")
    )
    if output_url:
        print(f"\n[done] Image URL: {output_url}")
    else:
        print(f"\n[done] Final payload: {final}")


if __name__ == "__main__":
    asyncio.run(main())
