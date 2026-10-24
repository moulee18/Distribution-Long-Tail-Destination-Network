import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from contextvars import ContextVar

correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id_ctx", default=None)
job_id_ctx: ContextVar[Optional[str]] = ContextVar("job_id_ctx", default=None)

SECRET_PATTERNS = [
    re.compile(r'(?i)bearer\s+([A-Za-z0-9_\-\.]{8,})'),
    re.compile(r'(?i)(?:api_key|token|secret|password|authorization|auth_token)\s*[:=]\s*["\']?([^"\'\s&,]+)'),
]

def redact_secrets(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(r'***REDACTED***', redacted)
    return redacted

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        corr_id = correlation_id_ctx.get() or getattr(record, "correlation_id", None)
        job_id = job_id_ctx.get() or getattr(record, "job_id", None)
        
        msg = record.getMessage()
        if isinstance(msg, (dict, list)):
            msg_str = json.dumps(msg)
        else:
            msg_str = str(msg)
            
        safe_msg = redact_secrets(msg_str)
        
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": safe_msg,
        }
        if corr_id:
            log_entry["correlation_id"] = corr_id
        if job_id:
            log_entry["job_id"] = job_id
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("incubrix")
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False
    return logger

logger = setup_logging()
