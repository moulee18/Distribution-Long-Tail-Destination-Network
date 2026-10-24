import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.entities import (
    PublicationJob,
    PublicationAttempt,
    PublishedPost,
    Destination,
    DestinationRule,
    ContentItem,
    ContentRendition,
    Connection,
)
from backend.app.schemas.connector_contract import RenditionData, DestinationData, ConnectionData
from backend.app.rules.engine import rules_engine
from backend.app.connectors.registry import registry
from backend.app.tailoring.adapter import ai_service
from backend.app.core.errors import IncuBrixException, ErrorCode
from backend.app.core.logging import logger
from backend.app.core.config import settings

def compute_callback_signature(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

class PublishingOrchestrator:
    @staticmethod
    async def execute_job(job_id: str, db: AsyncSession) -> PublicationJob:
        start_time = time.time()
        stmt = select(PublicationJob).where(PublicationJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, f"Job {job_id} not found", 404)

        job.status = "running"
        job.progress = 5
        await db.commit()

        # Load content item
        stmt_c = select(ContentItem).where(ContentItem.id == job.content_item_id)
        res_c = await db.execute(stmt_c)
        content_item = res_c.scalar_one_or_none()
        if not content_item:
            job.status = "failed"
            job.error_summary = "Content item not found"
            await db.commit()
            return job

        # Load publication attempts
        stmt_a = select(PublicationAttempt).where(PublicationAttempt.job_id == job_id)
        res_a = await db.execute(stmt_a)
        attempts = list(res_a.scalars().all())

        total = len(attempts)
        job.total_destinations = total
        completed = 0
        total_cost_usd = 0.0
        warnings: List[str] = []

        for i, attempt in enumerate(attempts):
            dest_stmt = select(Destination).where(Destination.id == attempt.destination_id)
            dest_res = await db.execute(dest_stmt)
            dest = dest_res.scalar_one_or_none()
            if not dest:
                attempt.status = "failed"
                attempt.error_code = ErrorCode.RESOURCE_NOT_FOUND.value
                attempt.error_message = f"Destination {attempt.destination_id} not found"
                continue

            # Load rules
            rule_stmt = select(DestinationRule).where(DestinationRule.destination_id == dest.id)
            rule_res = await db.execute(rule_stmt)
            rule = rule_res.scalar_one_or_none()

            # Load connection
            conn_stmt = select(Connection).where(Connection.destination_id == dest.id)
            conn_res = await db.execute(conn_stmt)
            connection = conn_res.scalar_one_or_none()
            if not connection:
                # Create default connection
                connection = Connection(
                    destination_id=dest.id,
                    connector_key=dest.connector_key,
                    settings={"base_url": dest.url, "simulation": settings.SIMULATION_MODE},
                )
                db.add(connection)
                await db.flush()

            # Step 1: Tailor content for destination
            tailoring_res = ai_service.tailor(
                title=content_item.title,
                body=content_item.body,
                connector_key=dest.connector_key,
                tags=content_item.tags or [],
                canonical_url=content_item.canonical_url,
                is_promotional=content_item.is_promotional,
                contains_ai_content=content_item.contains_ai_content,
                ai_disclosure=content_item.ai_disclosure_statement,
                destination_language=dest.language or "en",
            )
            total_cost_usd += tailoring_res.cost_usd
            rendition_data = tailoring_res.rendition

            # Persist rendition
            rendition_rec = ContentRendition(
                content_item_id=content_item.id,
                destination_id=dest.id,
                connector_key=dest.connector_key,
                title=rendition_data.title,
                body=rendition_data.body,
                tags=rendition_data.tags,
                canonical_url=rendition_data.canonical_url,
            )
            db.add(rendition_rec)
            await db.flush()
            attempt.rendition_id = rendition_rec.id

            # Step 2: Validate destination rules
            rule_eval = rules_engine.evaluate(
                destination=dest,
                rule=rule,
                rendition=rendition_data,
                last_posted_at=dest.last_posted_at,
                auto_fix_disclosure=True,
            )
            attempt.rule_decision = rule_eval.decision
            attempt.rule_reasons = rule_eval.reasons

            if rule_eval.decision == "BLOCKED":
                attempt.status = "blocked"
                attempt.error_code = ErrorCode.DEST_SPEC_VIOLATION.value
                attempt.error_message = "; ".join(rule_eval.reasons)
                completed += 1
                job.progress = int((completed / total) * 90) + 5
                await db.commit()
                continue

            if rule_eval.decision == "RESCHEDULED":
                attempt.status = "retry_scheduled"
                attempt.scheduled_for = rule_eval.earliest_eligible_time
                attempt.error_code = ErrorCode.DEST_RULE_FREQUENCY_CAP.value
                attempt.error_message = "; ".join(rule_eval.reasons)
                completed += 1
                job.progress = int((completed / total) * 90) + 5
                await db.commit()
                continue

            # Update rendition if auto-disclosure or tailoring adjusted it
            if rule_eval.modified_rendition:
                rendition_data = rule_eval.modified_rendition

            # Step 3: Check consecutive failures (Circuit Breaker)
            if connection.consecutive_failures >= settings.CONSECUTIVE_FAILURE_LIMIT:
                attempt.status = "failed"
                attempt.error_code = ErrorCode.PLATFORM_UNAVAILABLE.value
                attempt.error_message = f"Circuit breaker: stopped calling after {connection.consecutive_failures} consecutive platform failures."
                completed += 1
                job.progress = int((completed / total) * 90) + 5
                await db.commit()
                continue

            # Step 4: Invoke Connector
            connector = registry.get_connector(dest.connector_key)
            dest_dto = DestinationData(
                name=dest.name,
                url=dest.url,
                platform_key=dest.platform_key,
                surface=dest.surface,
                category=dest.category,
                audience_tags=dest.audience_tags or [],
                language=dest.language or "en",
                geo=dest.geo or "GLOBAL",
                est_audience=dest.est_audience or 0,
                rules_url=dest.rules_url,
                frequency_cap=dest.frequency_cap,
                self_promo_allowed=dest.self_promo_allowed,
                link_policy=dest.link_policy,
                disclosure_required=dest.disclosure_required,
                automation_allowed=dest.automation_allowed,
                connector_key=dest.connector_key,
                relevance_score=dest.relevance_score,
                level=dest.level,
            )
            conn_dto = ConnectionData(
                credentials=connection.encrypted_credentials or {},
                settings=connection.settings or {},
            )

            # Idempotency key per destination publication attempt
            item_idempotency_key = f"{job.idempotency_key or job.id}:{dest.id}"

            # SAFE RETRY CHECK:
            # Check if this post ID or idempotency key was already published
            existing_post_stmt = select(PublishedPost).where(
                PublishedPost.destination_id == dest.id,
                PublishedPost.attempt_id == attempt.id,
            )
            existing_post_res = await db.execute(existing_post_stmt)
            existing_post = existing_post_res.scalar_one_or_none()
            if existing_post and existing_post.status == "live":
                logger.info(f"Safe retry: post already exists for destination {dest.id}, skipping publish call.")
                attempt.status = "published"
                attempt.platform_post_id = existing_post.platform_post_id
                attempt.live_url = existing_post.live_url
                completed += 1
                job.progress = int((completed / total) * 90) + 5
                await db.commit()
                continue

            try:
                if rule_eval.requires_assisted or dest.connector_key == "assisted":
                    # Assisted path
                    assist_res = await connector.build_assist_pack(rendition_data, dest_dto)
                    attempt.status = "manual_action_required"
                    attempt.assist_pack = assist_res.model_dump()
                    attempt.platform_post_id = f"assist_{item_idempotency_key[:8]}"
                    attempt.live_url = dest.url
                else:
                    # Native or protocol publish
                    pub_res = await connector.publish(
                        rendition=rendition_data,
                        destination=dest_dto,
                        connection=conn_dto,
                        idempotency_key=item_idempotency_key,
                    )
                    attempt.platform_post_id = pub_res.platform_post_id
                    attempt.live_url = pub_res.live_url
                    attempt.status = pub_res.status  # e.g. "live" or "published"

                    # Verify status immediately
                    if pub_res.status in ("live", "published"):
                        status_res = await connector.get_status(pub_res.platform_post_id, conn_dto)
                        if status_res.status not in ("live", "published"):
                            attempt.status = "verification_failed"
                            warnings.append(f"Post created on {dest.name} but verification returned {status_res.status}")
                        else:
                            attempt.status = "published"
                            dest.last_posted_at = datetime.now(timezone.utc)
                            # Create published post record
                            pub_post = PublishedPost(
                                attempt_id=attempt.id,
                                destination_id=dest.id,
                                platform_post_id=pub_res.platform_post_id,
                                live_url=pub_res.live_url,
                                status="live",
                            )
                            db.add(pub_post)

                connection.consecutive_failures = 0
            except IncuBrixException as ie:
                attempt.status = "failed"
                attempt.error_code = ie.code.value
                attempt.error_message = ie.message
                connection.consecutive_failures += 1
                if ie.code == ErrorCode.CONNECTION_AUTH_EXPIRED:
                    connection.auth_expired = True
                warnings.append(f"Failed publishing to {dest.name}: [{ie.code.value}] {ie.message}")
            except Exception as e:
                attempt.status = "failed"
                attempt.error_code = ErrorCode.PLATFORM_UNAVAILABLE.value
                attempt.error_message = str(e)
                connection.consecutive_failures += 1
                warnings.append(f"Unexpected error publishing to {dest.name}: {str(e)}")

            completed += 1
            job.progress = int((completed / total) * 90) + 5
            await db.commit()

        # Finalize job
        all_statuses = [a.status for a in attempts]
        if all(s == "published" for s in all_statuses):
            job.status = "succeeded"
        elif all(s in ("failed", "blocked") for s in all_statuses):
            job.status = "failed"
        elif any(s in ("published", "manual_action_required") for s in all_statuses):
            job.status = "succeeded"
        else:
            job.status = "partial"

        job.progress = 100
        job.completed_destinations = completed
        elapsed = round(time.time() - start_time, 3)

        # Build Output Manifest (Integration Standard Point 9)
        job.output_manifest = {
            "incubrix_version": "1.0.0",
            "job_id": job.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_time_s": elapsed,
            "ai_provider": {
                "provider": "mock" if settings.SIMULATION_MODE else settings.AI_PROVIDER,
                "model": settings.AI_MODEL_NAME,
                "cost_usd": round(total_cost_usd, 6),
            },
            "warnings": warnings,
            "licence_rights": {
                "rights_retained": "Creator",
                "ai_generated": content_item.contains_ai_content,
                "commercial_usable": True,
                "open_source_compliance": "MIT / Apache-2.0 clean",
            },
        }
        await db.commit()

        # Handle callback URL if provided (Integration Standard Point 3)
        if job.callback_url:
            await PublishingOrchestrator._send_callback(job)

        return job

    @staticmethod
    async def _send_callback(job: PublicationJob):
        try:
            payload = {
                "job_id": job.id,
                "status": job.status,
                "progress": job.progress,
                "total_destinations": job.total_destinations,
                "completed_destinations": job.completed_destinations,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            body_bytes = json.dumps(payload).encode("utf-8")
            sig = compute_callback_signature(body_bytes, settings.SECRET_KEY)
            headers = {
                "Content-Type": "application/json",
                "X-IncuBrix-Signature": sig,
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(job.callback_url, content=body_bytes, headers=headers)
        except Exception as e:
            logger.warning(f"Failed to deliver callback to {job.callback_url}: {str(e)}")

orchestrator = PublishingOrchestrator()
