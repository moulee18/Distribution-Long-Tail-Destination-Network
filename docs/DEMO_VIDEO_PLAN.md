# Demo Video Recording Plan (Max 8 Minutes, Unedited)

This script outlines the exact 4-part flow required by Page 6-7 of the IncuBrix Assessment brief for the unedited screen recording.

---

## Segment 1: One Complete Successful End-to-End Run (0:00 – 2:30)
1. **Show Dashboard (`/ui/index.html`)**: Point out the live backend metrics and click **Load 165 Seed Destinations** (`POST /api/v1/catalogue/seed-full`).
2. **Destination Explorer**: Filter across `Discourse`, `Lemmy`, `Dev.to`, `Ghost`, `Webhook`, and `Assisted` destinations. Click **Certify** on a Discourse forum and inspect the live certification evidence (`L3`/`L4`, `cleanup_status: "deleted"`).
3. **Content Studio**: Create a new content item: *"How We Scaled Organic AI Video Distribution for SaaS Founders"* with tags `ai, video, saas, founders`, checking **Contains AI-Generated Material**.
4. **Publishing Workspace**:
   - Select the content item and click **Recommend Top Destinations**.
   - Highlight the ranked relevance scores (5.0 / 5.0) and eligibility explanations.
   - Select both a native destination (e.g., `Hugging Face Discuss` on Discourse) and a manual-only destination (`Hacker News - Show HN` on Assisted).
   - Click **Publish to Selected Destinations**.
   - Watch the real-time progress bar hit `100% (succeeded)` and inspect the `output_manifest`, the tailored Discourse discussion prompt, the automatically appended AI disclosure, and the Assisted pack (`manual_action_required`).

---

## Segment 2: Controlled Failure & Recovery (2:30 – 4:15)
1. **Rule Violation Block**: In Content Studio, create a promotional post (*"Get 50% Off Our Plan"* with **Contains Self-Promotion** checked) and attempt to publish to a community where `self_promo_allowed: false` (e.g., `PyTorch Discuss`). Show in **Publishing History** that the post is deterministically marked `blocked` (`DEST_SPEC_VIOLATION`) before touching the connector.
2. **Connector Kill Switch & Recovery**: Go to **Connector Management**, click **Disable Kill-Switch** on `slack`, show that calls return `CONNECTOR_DISABLED (403)`, then re-enable it.
3. **Idempotent Retry**: Re-submit the same publication request with the same `Idempotency-Key` and show that the exact same `job_id` is returned with **0 duplicate posts**.

---

## Segment 3: Automated Tests & CLI Batch Runner Executing (4:15 – 5:45)
1. Open the terminal and run:
   ```bash
   pytest backend/tests -v
   ```
   Show all **32 tests passing in ~3 seconds** (Connector Contract for all 9 connectors, all 12 Hard Cases, and Integration Standard).
2. Run the Integration Standard Batch Runner:
   ```bash
   python -m scripts.batch_runner --input fixtures/batch_inputs --output evidence/batch_outputs
   ```
   Open `evidence/batch_outputs/batch_summary.json` to show the structured JSON outputs and correlation IDs.

---

## Segment 4: Architecture & Design Decision in Code (5:45 – 7:30)
1. Open `manifests/discourse.yaml`, `backend/app/connectors/registry.py`, and `backend/app/api/connector_routes.py`.
2. Explain the **"One Connector, Many Destinations"** design: how `ConnectorRegistry` dynamically binds YAML manifests to `BaseConnector` implementations without coupling connectors to the database.
3. Open `backend/app/publishing/orchestrator.py` and `backend/app/rules/engine.py` to trace how `PublicationJob` → `RulesEngine.evaluate()` → `connector.publish()` → `connector.get_status()` → `PublishedPost` → `job.output_manifest` flows end-to-end.
