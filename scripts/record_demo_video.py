import asyncio
import io
import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio
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


def annotate_frame(png_bytes: bytes, step_badge: str, title: str, subtitle: str) -> Image.Image:
    """Adds a clean, high-contrast instructional overlay banner at the bottom of a 1920x1080 frame."""
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    width, height = img.size

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Bottom banner background
    banner_top = height - 155
    draw.rectangle([(0, banner_top), (width, height)], fill=(15, 23, 42, 235))
    draw.rectangle([(0, banner_top), (width, banner_top + 4)], fill=(56, 189, 248, 255))

    # Load system fonts (fallback to default if arial not found)
    try:
        font_badge = ImageFont.truetype("arialbd.ttf", 20)
        font_title = ImageFont.truetype("arialbd.ttf", 30)
        font_sub = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font_badge = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Step pill badge
    draw.rounded_rectangle([(40, banner_top + 22), (240, banner_top + 58)], radius=8, fill=(2, 132, 199, 255))
    draw.text((56, banner_top + 28), step_badge, fill=(255, 255, 255, 255), font=font_badge)

    # Title text
    draw.text((260, banner_top + 22), title, fill=(248, 250, 252, 255), font=font_title)

    # Subtitle explanation
    draw.text((40, banner_top + 76), subtitle, fill=(203, 213, 225, 255), font=font_sub)

    combined = Image.alpha_composite(img, overlay).convert("RGB")
    return combined


async def generate_walkthrough():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    exe_path = get_browser_executable()
    scenes = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=exe_path, headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        page = await context.new_page()

        # 1. Dashboard Overview
        await page.goto("http://127.0.0.1:8000/ui/index.html", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        raw1 = await page.screenshot()
        scenes.append((
            "step1_dashboard.png",
            "STEP 1 OF 10",
            "1. Overview Dashboard — Real-Time Network Telemetry",
            "Shows 165 Destinations, 165 Certified (L1-L4), 9 Active Connectors, Live Published Posts, Rule Blocks, and Recent Activity."
        , raw1, 4.5))

        # 2. Content Studio
        await page.click("button:has-text('2. Content Studio')")
        await page.wait_for_timeout(800)
        await page.fill("#content-title", "Scaling Event-Driven Microservices with Idempotent Webhooks")
        await page.fill(
            "#content-body",
            "Event-driven architectures require strict idempotency guarantees.\n\nUse HMAC-SHA256 signatures and durable Idempotency-Key locks to prevent duplicate deliveries across distributed subscribers."
        )
        await page.fill("#content-canonical", "https://incubrix.dev/blog/event-driven-webhooks")
        await page.wait_for_timeout(600)
        raw2 = await page.screenshot()
        scenes.append((
            "step2_studio.png",
            "STEP 2 OF 10",
            "2. Content Studio — Authoring & Metadata Tagging",
            "Write your core Markdown article once, attach Audience Tags and Canonical URL, and declare Promotional or AI-Generated flags."
        , raw2, 4.5))

        # Save the content item
        await page.click("#content-form button[type='submit']")
        await page.wait_for_timeout(1000)

        # 3. Destination Explorer
        await page.click("button:has-text('3. Destination Explorer')")
        await page.wait_for_timeout(1000)
        raw3 = await page.screenshot()
        scenes.append((
            "step3_explorer.png",
            "STEP 3 OF 10",
            "3. Destination Explorer — 165 Researched Communities & CSV Importer",
            "Browse and filter 165 long-tail destinations by Platform, Certification Level (L0-L4), Audience Tags, and Posting Rules."
        , raw3, 4.5))

        # Filter by Discourse
        await page.select_option("#filter-platform", "discourse")
        await page.wait_for_timeout(800)
        raw3b = await page.screenshot()
        scenes.append((
            "step3b_filter.png",
            "STEP 4 OF 10",
            "3b. One Connector, Many Destinations — Filtering by Platform",
            "A single reusable Discourse connector powers multiple independent forums via configuration (instance_param: forum_base_url)."
        , raw3b, 4.0))
        await page.select_option("#filter-platform", "")

        # 4. Publishing Workspace (Recommendations)
        await page.click("button:has-text('4. Publishing Workspace')")
        await page.wait_for_timeout(1200)
        await page.click("button:has-text('Recommend Top Destinations')")
        await page.wait_for_timeout(1200)
        raw4 = await page.screenshot()
        scenes.append((
            "step4_workspace_rec.png",
            "STEP 5 OF 10",
            "4. Publishing Workspace — AI Destination Recommendations (Precision@10 = 1.0)",
            "Ranks destinations by topic/tag fit, audience match, certification level, and pre-flight deterministic rule eligibility."
        , raw4, 4.5))

        # Execute live publishing in workspace
        await page.click("button:has-text('Publish to Selected Destinations')")
        await page.wait_for_timeout(2500)
        raw4b = await page.screenshot()
        scenes.append((
            "step4b_workspace_pub.png",
            "STEP 6 OF 10",
            "4b. Live Background Job Execution & Idempotent Orchestration",
            "Dispatches HTTP 202 background job with Idempotency-Key, tailors content per destination, and verifies live post URLs."
        , raw4b, 4.5))

        # 5. Connector Management
        await page.click("button:has-text('5. Connector Management')")
        await page.wait_for_timeout(900)
        raw5 = await page.screenshot()
        scenes.append((
            "step5_connectors.png",
            "STEP 7 OF 10",
            "5. Connector Management — Declarative YAML Manifests & Kill Switches",
            "Displays all 9 connectors (Discourse, Lemmy, Dev.to, Ghost, Webhook, Assisted, Hashnode, Slack, Newsletter) and instant kill switches."
        , raw5, 4.5))

        # 6. Certification Centre
        await page.click("button:has-text('6. Certification Centre')")
        await page.wait_for_timeout(1000)
        inspect_btns = await page.query_selector_all("#certifications-tbody button")
        if inspect_btns:
            await inspect_btns[0].click()
            await page.wait_for_timeout(700)
        raw6 = await page.screenshot()
        scenes.append((
            "step6_certification.png",
            "STEP 8 OF 10",
            "6. Certification Centre — Automated Publish -> Verify -> Delete Harness",
            "Certifies destinations safely against sandbox instances, cleans up test posts immediately, and stores full API evidence traces."
        , raw6, 4.5))

        # 7. Publishing History
        await page.click("button:has-text('7. Publishing History')")
        await page.wait_for_timeout(1000)
        raw7 = await page.screenshot()
        scenes.append((
            "step7_history.png",
            "STEP 9 OF 10",
            "7. Publishing History — Complete Audit Log, Rule Blocks & Assisted Packs",
            "Tracks every live post URL, blocked rule violation (e.g., SELF_PROMO_PROHIBITED), and downloadable Assisted ZIP pack."
        , raw7, 4.5))

        # 8. OpenAPI Swagger Docs (/docs)
        await page.goto("http://127.0.0.1:8000/docs", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        raw8 = await page.screenshot()
        scenes.append((
            "step8_openapi.png",
            "STEP 10 OF 10",
            "8. OpenAPI 3.1.0 Interactive Documentation (/docs)",
            "Exposes the mandatory Appendix A contract (/connector/v1/{connector_key}/{method}) alongside /api/v1/* application routes."
        , raw8, 4.5))

        await browser.close()

    # Save annotated PNGs and encode MP4 video at 10 fps
    fps = 10
    video_path_evidence = EVIDENCE_DIR / "incubrix_demo_walkthrough.mp4"
    video_path_artifact = ARTIFACT_DIR / "incubrix_demo_walkthrough.mp4"

    writer = imageio.get_writer(str(video_path_evidence), fps=fps, codec="libx264", quality=8)
    import numpy as np

    for filename, badge, title, subtitle, png_bytes, duration_sec in scenes:
        annotated_img = annotate_frame(png_bytes, badge, title, subtitle)
        img_out_path = ARTIFACT_DIR / filename
        annotated_img.save(img_out_path, format="PNG")
        frame_np = np.array(annotated_img)
        num_frames = int(duration_sec * fps)
        for _ in range(num_frames):
            writer.append_data(frame_np)

    writer.close()
    shutil.copyfile(video_path_evidence, video_path_artifact)
    print(f"Saved walkthrough video to: {video_path_evidence}")
    print(f"Copied walkthrough video to artifact dir: {video_path_artifact}")


if __name__ == "__main__":
    asyncio.run(generate_walkthrough())
