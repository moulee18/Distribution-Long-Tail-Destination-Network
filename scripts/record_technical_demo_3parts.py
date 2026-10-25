import asyncio
import io
import os
import shutil
from pathlib import Path
from PIL import Image
import imageio
import numpy as np
from playwright.async_api import async_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = ROOT_DIR / "evidence"
ARTIFACT_DIR = Path(r"C:\Users\moule\.gemini\antigravity\brain\5869f695-0d14-422c-90a1-effa36ecd8cd")

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def get_browser_executable() -> str:
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    raise RuntimeError("No local Chrome/Edge browser found.")


def format_time(seconds: float) -> str:
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:02d}:{secs:02d}"


def process_clean_frame(png_bytes: bytes, width: int = 1920, height: int = 1080) -> Image.Image:
    """Returns a clean, full-screen, unannotated screen capture (normal screencast video)."""
    raw = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    if raw.size != (width, height):
        raw = raw.resize((width, height), Image.Resampling.LANCZOS)
    return raw


async def record_technical_demo():
    """Technical Demo Video (Up to 5 min):
       1. One normal run
       2. A refresh on new input
       3. Recovery from one simple failure
    """
    print("\n--- Recording Technical Demo Video: 3 Parts (Normal Run, Refresh on New Input, Failure Recovery) ---")
    exe_path = get_browser_executable()
    scenes = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=exe_path, headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # =========================================================================
        # PART 1: ONE NORMAL RUN (~1m 30s)
        # =========================================================================

        # Scene 1: Dashboard Overview (20s)
        await page.goto("http://127.0.0.1:8000/ui/index.html", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        scenes.append({
            "part": "PART 1: NORMAL RUN",
            "name": "Dashboard Overview",
            "duration": 20.0,
            "bytes": await page.screenshot()
        })

        # Scene 2: Content Studio — Authoring standard post (22s)
        await page.click("button:has-text('2. Content Studio')")
        await page.wait_for_timeout(800)
        await page.fill("#content-title", "Building Resilient Event-Driven Microservices in Python")
        await page.fill("#content-body", "In distributed architectures, message delivery guarantees and idempotency are critical.\n\nIncuBrix verifies pre-flight destination rules and publishes across Discourse, Lemmy, Dev.to, and Ghost seamlessly.")
        await page.fill("#content-canonical", "https://incubrix.dev/blog/event-driven-microservices")
        await page.fill("#content-tags", "python, backend, architecture, apis")
        await page.wait_for_timeout(600)
        scenes.append({
            "part": "PART 1: NORMAL RUN",
            "name": "Content Studio Input",
            "duration": 22.0,
            "bytes": await page.screenshot()
        })

        # Save standard post
        await page.click("#content-form button[type='submit']")
        await page.wait_for_timeout(1000)

        # Scene 3: Publishing Workspace — Recommending & Pre-flight check (25s)
        await page.click("button:has-text('4. Publishing Workspace')")
        await page.wait_for_timeout(1000)
        await page.click("button:has-text('Recommend Top Destinations')")
        await page.wait_for_timeout(1500)
        scenes.append({
            "part": "PART 1: NORMAL RUN",
            "name": "Recommendations & Rules Pass",
            "duration": 25.0,
            "bytes": await page.screenshot()
        })

        # Scene 4: Live Publishing Job Execution & Status 100% (25s)
        await page.click("button:has-text('Publish to Selected Destinations')")
        await page.wait_for_timeout(3000)
        scenes.append({
            "part": "PART 1: NORMAL RUN",
            "name": "Publishing Progress 100% & Live Confirmation",
            "duration": 25.0,
            "bytes": await page.screenshot()
        })

        # =========================================================================
        # PART 2: A REFRESH ON NEW INPUT (~1m 15s)
        # =========================================================================

        # Scene 5: Content Studio — Providing brand new input with distinct tags (25s)
        await page.click("button:has-text('2. Content Studio')")
        await page.wait_for_timeout(800)
        await page.fill("#content-title", "Enterprise Cloud Migration & Kubernetes Cost Optimization")
        await page.fill("#content-body", "Migrating monolithic architectures to Kubernetes requires autoscaling, spot instances, and ingress policy automation.\n\nHere is our step-by-step technical guide for cloud and DevOps engineers.")
        await page.fill("#content-canonical", "https://incubrix.dev/blog/kubernetes-cloud-migration")
        await page.fill("#content-tags", "cloud, kubernetes, devops, aws, infrastructure")
        await page.wait_for_timeout(600)
        scenes.append({
            "part": "PART 2: REFRESH ON NEW INPUT",
            "name": "New Input Authoring",
            "duration": 25.0,
            "bytes": await page.screenshot()
        })

        # Save new input
        await page.click("#content-form button[type='submit']")
        await page.wait_for_timeout(1000)

        # Scene 6: Publishing Workspace — Refreshing recommendations on new input (30s)
        await page.click("button:has-text('4. Publishing Workspace')")
        await page.wait_for_timeout(1000)
        # Select the newly created content item
        await page.select_option("#pub-content-select", index=0)
        await page.wait_for_timeout(600)
        await page.click("button:has-text('Recommend Top Destinations')")
        await page.wait_for_timeout(1500)
        scenes.append({
            "part": "PART 2: REFRESH ON NEW INPUT",
            "name": "Dynamic Refresh on New Input",
            "duration": 30.0,
            "bytes": await page.screenshot()
        })

        # =========================================================================
        # PART 3: RECOVERY FROM ONE SIMPLE FAILURE (~1m 30s)
        # =========================================================================

        # Scene 7: Content Studio — Creating a post with self-promotion enabled (24s)
        await page.click("button:has-text('2. Content Studio')")
        await page.wait_for_timeout(800)
        await page.fill("#content-title", "Exclusive 50% Discount on Our Enterprise Cloud SaaS Tier")
        await page.fill("#content-body", "Sign up today with coupon code SAVE50 to get 50% off our commercial cloud SaaS tier. Visit https://example.com/pricing.")
        await page.fill("#content-canonical", "https://example.com/pricing")
        await page.fill("#content-tags", "saas, cloud, marketing, discount")
        await page.check("#content-promo")
        await page.wait_for_timeout(600)
        scenes.append({
            "part": "PART 3: FAILURE & RECOVERY",
            "name": "Triggering Failure: Self-Promotion Flag Enabled",
            "duration": 24.0,
            "bytes": await page.screenshot()
        })

        # Save promotional post
        await page.click("#content-form button[type='submit']")
        await page.wait_for_timeout(1000)

        # Scene 8: Publishing History — Showing failure caught by rules (28s)
        await page.click("button:has-text('7. Publishing History')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "part": "PART 3: FAILURE & RECOVERY",
            "name": "Failure Caught: Rules Engine Blocks Self-Promotion Pre-Flight",
            "duration": 28.0,
            "bytes": await page.screenshot()
        })

        # Scene 9: Recovery — Editing content to comply with non-promotional rules (25s)
        await page.click("button:has-text('2. Content Studio')")
        await page.wait_for_timeout(800)
        await page.fill("#content-title", "Architecture Patterns for Scalable Multi-Tenant Cloud Services")
        await page.fill("#content-body", "When designing multi-tenant architectures, isolating tenant data while sharing compute clusters requires strict namespace boundaries and role-based access control.\n\nHere is an in-depth architectural breakdown.")
        await page.uncheck("#content-promo")
        await page.wait_for_timeout(600)
        scenes.append({
            "part": "PART 3: FAILURE & RECOVERY",
            "name": "Recovery: Content Adjusted to Compliant Technical Post",
            "duration": 25.0,
            "bytes": await page.screenshot()
        })

        # Save recovered post
        await page.click("#content-form button[type='submit']")
        await page.wait_for_timeout(1000)

        # Scene 10: Successful Re-publish & Resolution (25s)
        await page.click("button:has-text('4. Publishing Workspace')")
        await page.wait_for_timeout(1000)
        await page.select_option("#pub-content-select", index=0)
        await page.click("button:has-text('Recommend Top Destinations')")
        await page.wait_for_timeout(1200)
        await page.click("button:has-text('Publish to Selected Destinations')")
        await page.wait_for_timeout(2500)
        scenes.append({
            "part": "PART 3: FAILURE & RECOVERY",
            "name": "Recovery Complete: Pre-flight Passes & Publishing Succeeds",
            "duration": 25.0,
            "bytes": await page.screenshot()
        })

        # Scene 11: Analytics & System Health Wrap-Up (15s)
        await page.click("button:has-text('8. Analytics')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "part": "PART 3: FAILURE & RECOVERY",
            "name": "Analytics Summary: Zero Spam, Safe Retries & System Health",
            "duration": 18.0,
            "bytes": await page.screenshot()
        })

        await browser.close()

    total_duration = sum(s["duration"] for s in scenes)
    total_time_str = format_time(total_duration)
    print(f"Total Technical Demo Video duration: {total_time_str} ({total_duration:.1f}s)")

    # Render clean 1080p video without banners (macro_block_size=1)
    fps = 6
    video_out_ev = EVIDENCE_DIR / "technical_demo_video.mp4"
    video_out_art = ARTIFACT_DIR / "technical_demo_video.mp4"
    writer = imageio.get_writer(
        str(video_out_ev),
        fps=fps,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        macro_block_size=1,
    )

    for sc in scenes:
        clean_img = process_clean_frame(sc["bytes"], width=1920, height=1080)
        frame_np = np.array(clean_img)
        frames_count = int(sc["duration"] * fps)
        for _ in range(frames_count):
            writer.append_data(frame_np)

    writer.close()
    shutil.copyfile(video_out_ev, video_out_art)
    print(f"Saved clean Technical Demo Video to: {video_out_ev}")


if __name__ == "__main__":
    asyncio.run(record_technical_demo())
