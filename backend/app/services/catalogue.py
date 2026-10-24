import csv
import io
import ipaddress
import re
import socket
import time
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.entities import Destination, DestinationRule
from backend.app.schemas.app_schemas import ImportSummary
from backend.app.core.logging import logger

VALID_LANGUAGES = {
    "en", "es", "fr", "de", "it", "pt", "nl", "ja", "zh", "ko", "ru", "hi", "ar", "pl", "sv", "no", "da", "fi"
}

def normalize_url(raw_url: str) -> str:
    url = raw_url.strip()
    if not url.lower().startswith("http://") and not url.lower().startswith("https://"):
        url = "https://" + url
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    # Strip default ports
    if (scheme == "http" and netloc.endswith(":80")) or (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc.rsplit(":", 1)[0]
    path = parsed.path.rstrip("/")
    normalized = f"{scheme}://{netloc}{path}"
    return normalized

def is_safe_external_url(url: str, allow_local_for_tests: bool = True) -> Tuple[bool, str]:
    """
    SSRF Protection: Ensure the URL does not resolve to loopback, private,
    link-local or reserved IP addresses.
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL"

        host_lower = hostname.lower()
        if host_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal") or host_lower.endswith(".internal") or host_lower.endswith(".local"):
            if allow_local_for_tests and host_lower in ("localhost", "127.0.0.1"):
                return True, "Safe (test environment local allowed)"
            return False, "SSRF: Localhost / internal hostname addresses are blocked"

        # Check if hostname is an IP literal
        try:
            ip = ipaddress.ip_address(host_lower)
            if ip.is_link_local or ip.is_private or ip.is_reserved or ip.is_multicast:
                return False, f"SSRF: Target IP {host_lower} is a private, link-local, or reserved network address"
            if ip.is_loopback and not allow_local_for_tests:
                return False, f"SSRF: Loopback IP {host_lower} is blocked"
        except ValueError:
            pass

        return True, "Safe"
    except Exception as e:
        return False, f"URL parse error: {str(e)}"

class CatalogueService:
    @staticmethod
    async def import_csv_data(
        csv_content: str,
        db: AsyncSession,
        allow_local: bool = True,
    ) -> ImportSummary:
        start_time = time.time()
        reader = csv.DictReader(io.StringIO(csv_content))
        
        total_rows = 0
        imported_count = 0
        duplicate_count = 0
        error_count = 0
        errors: List[Dict[str, Any]] = []

        # Cache existing normalized URLs
        existing_stmt = select(Destination.platform_key, Destination.normalized_url)
        existing_res = await db.execute(existing_stmt)
        seen_in_db = set(existing_res.all())  # set of (platform_key, normalized_url)
        seen_in_batch = set()

        for row_idx, row in enumerate(reader, start=2):  # row 1 is header
            total_rows += 1
            name = (row.get("name") or "").strip()
            raw_url = (row.get("url") or "").strip()
            platform_key = (row.get("platform_key") or "").strip().lower()
            connector_key = (row.get("connector_key") or platform_key).strip().lower()
            lang = (row.get("language") or "en").strip().lower()

            # 1. Required fields
            if not name or not raw_url or not platform_key:
                error_count += 1
                errors.append({
                    "row": row_idx,
                    "error": "Missing required fields (name, url, or platform_key)",
                    "data": row,
                })
                continue

            # 2. URL syntax & normalisation
            try:
                norm_url = normalize_url(raw_url)
            except Exception as e:
                error_count += 1
                errors.append({
                    "row": row_idx,
                    "error": f"Invalid URL syntax: {str(e)}",
                    "data": row,
                })
                continue

            # 3. SSRF Protection check
            safe, ssrf_msg = is_safe_external_url(norm_url, allow_local_for_tests=allow_local)
            if not safe:
                error_count += 1
                errors.append({
                    "row": row_idx,
                    "error": ssrf_msg,
                    "data": row,
                })
                continue

            # 4. Language validation
            if lang and lang not in VALID_LANGUAGES:
                error_count += 1
                errors.append({
                    "row": row_idx,
                    "error": f"Unsupported or invalid language code: '{lang}'",
                    "data": row,
                })
                continue

            # 5. Duplicate detection
            key_pair = (platform_key, norm_url)
            if key_pair in seen_in_db or key_pair in seen_in_batch:
                duplicate_count += 1
                errors.append({
                    "row": row_idx,
                    "error": f"Duplicate destination: ({platform_key}, {norm_url}) already exists",
                    "data": row,
                })
                continue

            seen_in_batch.add(key_pair)

            # Parse tags
            raw_tags = row.get("audience_tags", "")
            tags = [t.strip().lower() for t in raw_tags.split(";") if t.strip()] if raw_tags else []

            # Parse bools
            self_promo = row.get("self_promo_allowed", "true").lower() in ("true", "1", "yes")
            disclosure = row.get("disclosure_required", "false").lower() in ("true", "1", "yes")
            automation = row.get("automation_allowed", "true").lower() in ("true", "1", "yes")
            
            # Scores
            try:
                rel_score = float(row.get("relevance_score", 3.0))
            except ValueError:
                rel_score = 3.0

            try:
                est_aud = int(row.get("est_audience", 0))
            except ValueError:
                est_aud = 0

            dest = Destination(
                name=name,
                url=raw_url,
                normalized_url=norm_url,
                platform_key=platform_key,
                connector_key=connector_key,
                surface=row.get("surface", "post"),
                category=row.get("category", "General"),
                audience_tags=tags,
                language=lang,
                geo=row.get("geo", "GLOBAL"),
                est_audience=est_aud,
                rules_url=row.get("rules_url"),
                frequency_cap=row.get("frequency_cap", "daily"),
                self_promo_allowed=self_promo,
                link_policy=row.get("link_policy", "allowed"),
                disclosure_required=disclosure,
                automation_allowed=automation,
                relevance_score=rel_score,
                relevance_reason=row.get("relevance_reason", "Imported via CSV"),
                level=row.get("level", "L0"),
            )
            db.add(dest)
            imported_count += 1

        await db.commit()
        elapsed = round(time.time() - start_time, 3)

        return ImportSummary(
            total_rows=total_rows,
            imported_count=imported_count,
            duplicate_count=duplicate_count,
            error_count=error_count,
            duration_seconds=elapsed,
            errors=errors,
        )

catalogue_service = CatalogueService()
