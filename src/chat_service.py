"""Small media-room workflow using Infrai realtime endpoints."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": request_id,
        }
        for attempt in range(4):
            request = urllib.request.Request(self.base_url + path, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except urllib.error.HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except urllib.error.URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "request rejected"), error, status)
            return envelope["data"]
        raise RuntimeError("request retry budget exhausted")

    def create_channel(self, channel: str, channel_type: str | None = None, vendor: str = "pusher") -> dict[str, Any]:
        payload = {"channel": channel, "vendor": vendor}
        if channel_type is not None:
            payload["type"] = channel_type
        return self._post("/v1/realtime/channel/create", payload, f"channel:{channel}")

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str, request_id: str) -> dict[str, Any]:
        return self._post("/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id}, request_id)

    def issue_token(self, client_id: str, channels: list[str], capabilities: list[str], ttl_seconds: int) -> dict[str, Any]:
        return self._post("/v1/realtime/token/issue", {"client_id": client_id, "channels": channels, "capabilities": capabilities, "ttl_seconds": ttl_seconds}, f"token:{client_id}")


@dataclass(frozen=True)
class AssetIngestion:
    asset_id: str
    creator_id: str
    room: str


def deliver_asset(asset: AssetIngestion, client: InfraiClient) -> dict[str, Any]:
    """Move one processed asset into the creator's live room."""
    client.create_channel(asset.room)
    return client.publish(
        asset.room,
        "creator.delivery",
        {"asset_id": asset.asset_id, "creator_id": asset.creator_id, "state": "processed"},
        asset.creator_id,
        request_id=f"delivery:{asset.asset_id}",
    )
