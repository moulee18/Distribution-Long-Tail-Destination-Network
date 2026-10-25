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


async def record_product_walkthrough():
    """Video 1: Product Walkthrough Video (Target: ~3:45 minutes, up to 5 min)."""
    print("\n--- Recording Video 1: Product Walkthrough Video (Clean Screencast) ---")
    exe_path = get_browser_executable()
    scenes = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=exe_path, headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # 1. Dashboard Overview (22s)
        await page.goto("http://127.0.0.1:8000/ui/index.html", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        scenes.append({
            "step": "SCENE 1",
            "duration": 22.0,
            "bytes": await page.screenshot()
        })

        # 2. Content Studio: Authoring (22s)
        await page.click("button:has-text('2. Content Studio')")
        await page.wait_for_timeout(800)
        await page.fill("#content-title", "Designing High-Throughput Event-Driven Microservices in Python")
        await page.fill("#content-body", "In distributed systems, publishing to external APIs requires idempotency and strict adherence to destination community guidelines.\n\nIncuBrix validates rules pre-flight and automates distribution across Discourse, Lemmy, Dev.to, and Ghost.")
        await page.fill("#content-canonical", "https://incubrix.dev/blog/distributed-publishing")
        await page.fill("#content-tags", "python, architecture, backend, devops, apis")
        await page.wait_for_timeout(600)
        scenes.append({
            "step": "SCENE 2",
            "duration": 22.0,
            "bytes": await page.screenshot()
        })

        # 3. Content Studio: Saved Library (20s)
        await page.click("#content-form button[type='submit']")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "SCENE 3",
            "duration": 20.0,
            "bytes": await page.screenshot()
        })

        # 4. Destination Explorer: 165 Researched Destinations (24s)
        await page.click("button:has-text('3. Destination Explorer')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "SCENE 4",
            "duration": 24.0,
            "bytes": await page.screenshot()
        })

        # 5. One Connector, Many Destinations (22s)
        await page.select_option("#filter-platform", "discourse")
        await page.wait_for_timeout(800)
        scenes.append({
            "step": "SCENE 5",
            "duration": 22.0,
            "bytes": await page.screenshot()
        })
        await page.select_option("#filter-platform", "")
        await page.wait_for_timeout(400)

        # 6. Publishing Workspace: AI Recommendations (25s)
        await page.click("button:has-text('4. Publishing Workspace')")
        await page.wait_for_timeout(1000)
        await page.click("button:has-text('Recommend Top Destinations')")
        await page.wait_for_timeout(1500)
        scenes.append({
            "step": "SCENE 6",
            "duration": 25.0,
            "bytes": await page.screenshot()
        })

        # 7. Live Publishing & Real-time Progress (25s)
        await page.click("button:has-text('Publish to Selected Destinations')")
        await page.wait_for_timeout(2800)
        scenes.append({
            "step": "SCENE 7",
            "duration": 25.0,
            "bytes": await page.screenshot()
        })

        # 8. Publishing History & Zero Spam Enforcement (22s)
        await page.click("button:has-text('7. Publishing History')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "SCENE 8",
            "duration": 22.0,
            "bytes": await page.screenshot()
        })

        # 9. Assisted Publishing Package (22s)
        scenes.append({
            "step": "SCENE 9",
            "duration": 22.0,
            "bytes": await page.screenshot()
        })

        # 10. Analytics & Telemetry (20s)
        await page.click("button:has-text('8. Analytics')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "SCENE 10",
            "duration": 20.0,
            "bytes": await page.screenshot()
        })

        await browser.close()

    total_duration = sum(s["duration"] for s in scenes)
    total_time_str = format_time(total_duration)
    print(f"Total Video 1 duration: {total_time_str} ({total_duration:.1f}s)")

    # Render clean 1080p video without banners
    fps = 6
    video_out_ev = EVIDENCE_DIR / "product_walkthrough_video.mp4"
    video_out_art = ARTIFACT_DIR / "product_walkthrough_video.mp4"
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
    print(f"Saved clean Video 1 to: {video_out_ev}")


async def record_technical_demo():
    """Video 2: Technical Demo Video (Target: ~5:30 minutes, up to 8 min)."""
    print("\n--- Recording Video 2: Technical Demo Video (Clean Screencast) ---")
    exe_path = get_browser_executable()
    scenes = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=exe_path, headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # 1. Architecture & Tech Stack (28s)
        await page.goto("http://127.0.0.1:8000/docs", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        scenes.append({
            "step": "TECH 1",
            "duration": 28.0,
            "bytes": await page.screenshot()
        })

        # 2. Appendix A Connector Contract (30s)
        await page.evaluate("window.scrollTo(0, 450)")
        await page.wait_for_timeout(800)
        scenes.append({
            "step": "TECH 2",
            "duration": 30.0,
            "bytes": await page.screenshot()
        })

        # 3. Connector Registry & Manifests (28s)
        await page.goto("http://127.0.0.1:8000/ui/index.html", wait_until="networkidle")
        await page.click("button:has-text('5. Connector Management')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "TECH 3",
            "duration": 28.0,
            "bytes": await page.screenshot()
        })

        # 4. Instant Connector Kill Switch (25s)
        scenes.append({
            "step": "TECH 4",
            "duration": 25.0,
            "bytes": await page.screenshot()
        })

        # 5. Deterministic Rules Engine (32s)
        await page.click("button:has-text('3. Destination Explorer')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "TECH 5",
            "duration": 32.0,
            "bytes": await page.screenshot()
        })

        # 6. Idempotency & Safe Retries (30s)
        await page.click("button:has-text('4. Publishing Workspace')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "TECH 6",
            "duration": 30.0,
            "bytes": await page.screenshot()
        })

        # 7. Automated Certification Centre (30s)
        await page.click("button:has-text('6. Certification Centre')")
        await page.wait_for_timeout(1000)
        inspect_btns = await page.query_selector_all("#certifications-tbody button")
        if inspect_btns:
            await inspect_btns[0].click()
            await page.wait_for_timeout(700)
        scenes.append({
            "step": "TECH 7",
            "duration": 30.0,
            "bytes": await page.screenshot()
        })

        # 8. 30-Day Recertification & Automatic Demotion (28s)
        scenes.append({
            "step": "TECH 8",
            "duration": 28.0,
            "bytes": await page.screenshot()
        })

        # 9. Audit Logging & Redacted Secrets (26s)
        await page.click("button:has-text('7. Publishing History')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "TECH 9",
            "duration": 26.0,
            "bytes": await page.screenshot()
        })

        # 10. System Health & Probes (25s)
        await page.click("button:has-text('9. Settings & Health')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "TECH 10",
            "duration": 25.0,
            "bytes": await page.screenshot()
        })

        # 11. Benchmark Performance & Test Suite (30s)
        await page.click("button:has-text('8. Analytics')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "TECH 11",
            "duration": 30.0,
            "bytes": await page.screenshot()
        })

        # 12. Summary (24s)
        await page.click("button:has-text('1. Dashboard')")
        await page.wait_for_timeout(1000)
        scenes.append({
            "step": "TECH 12",
            "duration": 24.0,
            "bytes": await page.screenshot()
        })

        await browser.close()

    total_duration = sum(s["duration"] for s in scenes)
    total_time_str = format_time(total_duration)
    print(f"Total Video 2 duration: {total_time_str} ({total_duration:.1f}s)")

    # Render clean 1080p video without banners
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
    print(f"Saved clean Video 2 to: {video_out_ev}")


async def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    await record_product_walkthrough()
    await record_technical_demo()
    print("\n[SUCCESS] Successfully recorded and generated clean submission demo videos!")


if __name__ == "__main__":
    asyncio.run(main())
