from enum import Enum
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

class ErrorCode(str, Enum):
    DEST_SPEC_VIOLATION = "DEST_SPEC_VIOLATION"
    DEST_RULE_FREQUENCY_CAP = "DEST_RULE_FREQUENCY_CAP"
    CONNECTION_AUTH_EXPIRED = "CONNECTION_AUTH_EXPIRED"
    PLATFORM_RATE_LIMIT = "PLATFORM_RATE_LIMIT"
    PLATFORM_QUOTA_EXHAUSTED = "PLATFORM_QUOTA_EXHAUSTED"
    PLATFORM_CONTENT_REJECTED = "PLATFORM_CONTENT_REJECTED"
    PLATFORM_UNAVAILABLE = "PLATFORM_UNAVAILABLE"
    CONNECTOR_DISABLED = "CONNECTOR_DISABLED"
    
    # System and Request errors
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

RETRYABLE_MAP: Dict[ErrorCode, bool] = {
    ErrorCode.DEST_SPEC_VIOLATION: False,
    ErrorCode.DEST_RULE_FREQUENCY_CAP: True,  # Can retry later after window
    ErrorCode.CONNECTION_AUTH_EXPIRED: False, # Needs reconnect
    ErrorCode.PLATFORM_RATE_LIMIT: True,      # Can retry after reset time
    ErrorCode.PLATFORM_QUOTA_EXHAUSTED: True, # Can retry next window
    ErrorCode.PLATFORM_CONTENT_REJECTED: False,
    ErrorCode.PLATFORM_UNAVAILABLE: True,
    ErrorCode.CONNECTOR_DISABLED: False,
    ErrorCode.IDEMPOTENCY_CONFLICT: False,
    ErrorCode.RESOURCE_NOT_FOUND: False,
    ErrorCode.VALIDATION_ERROR: False,
    ErrorCode.INTERNAL_ERROR: False,
}

class IncuBrixException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
        retryable: Optional[bool] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.retryable = retryable if retryable is not None else RETRYABLE_MAP.get(code, False)
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "retryable": self.retryable,
                "details": self.details,
            }
        }

    def to_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status_code, content=self.to_dict())
