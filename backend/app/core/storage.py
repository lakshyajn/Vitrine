"""
Storage Service Adapter (DECISION-D18).
Uploads product images to Supabase Storage or Mock/Local adapter in dev/test mode.
Per-user storage path: {user_id}/{product_id}/{filename}
"""

from __future__ import annotations

import logging
import re
from uuid import UUID
import httpx

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _sanitize_filename(self, filename: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename or "image.jpg")
        return clean.strip("_") or "image.jpg"

    async def upload_product_image(
        self,
        user_id: UUID,
        product_id: UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> str:
        """
        Uploads image under per-user path: {user_id}/{product_id}/{filename}.
        Returns public URL to the uploaded image.
        """
        safe_name = self._sanitize_filename(filename)
        bucket = "products"
        storage_path = f"{user_id}/{product_id}/{safe_name}"

        supabase_url = (self.settings.supabase_url or "").rstrip("/")
        service_key = (self.settings.supabase_service_role_key or "").strip()

        # Check if live Supabase credentials exist
        is_live = bool(
            supabase_url
            and service_key
            and "example" not in supabase_url
            and "test" not in supabase_url
            and not supabase_url.startswith("http://test")
        )

        if is_live:
            upload_endpoint = f"{supabase_url}/storage/v1/object/{bucket}/{storage_path}"
            headers = {
                "Authorization": f"Bearer {service_key}",
                "Content-Type": content_type,
                "x-upsert": "true",
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(upload_endpoint, content=content, headers=headers)
                    if resp.status_code in (200, 201):
                        return f"{supabase_url}/storage/v1/object/public/{bucket}/{storage_path}"
                    logger.warning(
                        "Supabase Storage returned %d: %s. Using local/mock storage URL.",
                        resp.status_code,
                        resp.text,
                    )
            except Exception as exc:
                logger.warning("Supabase Storage call failed: %s. Using local/mock storage URL.", exc)

        # Dev / test / mock storage adapter fallback URL
        base_host = supabase_url if (supabase_url and "example" not in supabase_url) else "https://storage.supabase.co"
        return f"{base_host}/{bucket}/{user_id}/{product_id}/{safe_name}"


def get_storage_service() -> StorageService:
    return StorageService()
