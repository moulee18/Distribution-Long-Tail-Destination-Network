import os
import yaml
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SurfaceSpec(BaseModel):
    title_max_chars: int = 255
    body_max_chars: int = 32000
    links_allowed: bool = True
    canonical_url_allowed: bool = False
    max_tags: Optional[int] = None
    media_supported: List[str] = Field(default_factory=list)

class Surface(BaseModel):
    key: str
    content_types: List[str]
    spec: SurfaceSpec

class RateLimits(BaseModel):
    requests: int = 60
    per_seconds: int = 60

class ConnectorManifest(BaseModel):
    key: str
    version: str = "1.0.0"
    tier: str  # native | protocol | bridge | feed | assisted
    auth: str  # oauth2 | api_key | bot_token | none
    surfaces: List[Surface]
    rate_limits: Dict[str, RateLimits] = Field(default_factory=dict)
    capabilities: List[str] = Field(default_factory=list)
    error_map: Dict[str, str] = Field(default_factory=dict)
    instance_param: str = "none"

def load_manifest(yaml_path: str) -> ConnectorManifest:
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Manifest file not found: {yaml_path}")
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return ConnectorManifest(**data)
