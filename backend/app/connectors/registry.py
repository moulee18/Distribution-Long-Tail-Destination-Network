import os
import glob
from typing import Dict, List, Optional, Type

from backend.app.connectors.base.connector import BaseConnector
from backend.app.connectors.base.manifest import ConnectorManifest, load_manifest
from backend.app.connectors.discourse.connector import DiscourseConnector
from backend.app.connectors.lemmy.connector import LemmyConnector
from backend.app.connectors.devto.connector import DevtoConnector
from backend.app.connectors.ghost.connector import GhostConnector
from backend.app.connectors.webhook.connector import WebhookConnector
from backend.app.connectors.assisted.connector import AssistedConnector
from backend.app.connectors.hashnode.connector import HashnodeConnector
from backend.app.connectors.slack.connector import SlackConnector
from backend.app.connectors.newsletter.connector import NewsletterConnector
from backend.app.core.errors import IncuBrixException, ErrorCode
from backend.app.core.logging import logger

CONNECTOR_CLASSES: Dict[str, Type[BaseConnector]] = {
    "discourse": DiscourseConnector,
    "lemmy": LemmyConnector,
    "devto": DevtoConnector,
    "ghost": GhostConnector,
    "webhook": WebhookConnector,
    "assisted": AssistedConnector,
    "hashnode": HashnodeConnector,
    "slack": SlackConnector,
    "newsletter": NewsletterConnector,
}

class ConnectorRegistry:
    def __init__(self):
        self._manifests: Dict[str, ConnectorManifest] = {}
        self._connectors: Dict[str, BaseConnector] = {}

    def load_manifests(self, manifests_dir: str):
        yaml_files = glob.glob(os.path.join(manifests_dir, "*.yaml")) + glob.glob(os.path.join(manifests_dir, "*.yml"))
        for path in yaml_files:
            try:
                manifest = load_manifest(path)
                self._manifests[manifest.key] = manifest
                cls = CONNECTOR_CLASSES.get(manifest.key)
                if cls:
                    self._connectors[manifest.key] = cls(manifest)
                    logger.info(f"Registered connector: {manifest.key} (tier: {manifest.tier})")
                else:
                    logger.warning(f"No connector implementation found for key: {manifest.key}")
            except Exception as e:
                logger.error(f"Failed to load connector manifest from {path}: {str(e)}")

    def get_connector(self, key: str) -> BaseConnector:
        connector = self._connectors.get(key)
        if not connector:
            raise IncuBrixException(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message=f"Connector '{key}' not found in registry",
                status_code=404,
            )
        if not connector.enabled:
            raise IncuBrixException(
                code=ErrorCode.CONNECTOR_DISABLED,
                message=f"Connector '{key}' is currently disabled by administrator kill switch",
                status_code=403,
            )
        return connector

    def get_manifest(self, key: str) -> ConnectorManifest:
        manifest = self._manifests.get(key)
        if not manifest:
            raise IncuBrixException(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message=f"Manifest for connector '{key}' not found",
                status_code=404,
            )
        return manifest

    def list_connectors(self) -> List[Dict]:
        res = []
        for key, m in self._manifests.items():
            conn = self._connectors.get(key)
            res.append({
                "key": m.key,
                "version": m.version,
                "tier": m.tier,
                "auth": m.auth,
                "capabilities": m.capabilities,
                "surfaces": [s.model_dump() for s in m.surfaces],
                "enabled": conn.enabled if conn else False,
            })
        return res

    def set_enabled(self, key: str, enabled: bool):
        conn = self._connectors.get(key)
        if not conn:
            raise IncuBrixException(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message=f"Connector '{key}' not found",
                status_code=404,
            )
        conn.enabled = enabled
        logger.info(f"Connector {key} enabled state set to: {enabled}")

registry = ConnectorRegistry()
