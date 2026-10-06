from __future__ import annotations

import hashlib
import json
import os
from typing import Any


class RedisCache:
    """
    Small Redis JSON cache used for parsed-query results.

    Redis is deliberately treated as a cache only.
    PostgreSQL remains authoritative for catalogue data.
    """

    def __init__(
        self,
        url: str | None = None,
        ttl_seconds: int = 3600,
    ) -> None:

        import redis

        self.url = url or os.getenv(
            "REDIS_URL",
            "redis://127.0.0.1:6379/0",
        )

        self.ttl_seconds = ttl_seconds

        self.client = redis.Redis.from_url(
            self.url,
            decode_responses=True,
        )

    @staticmethod
    def _key(query: str) -> str:
        normalized = " ".join(query.strip().split()).lower()

        digest = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        return f"fashion:parsed-query:{digest}"

    def get_json(
        self,
        query: str,
    ) -> dict[str, Any] | None:

        value = self.client.get(
            self._key(query)
        )

        if value is None:
            return None

        return json.loads(value)

    def set_json(
        self,
        query: str,
        value: dict[str, Any],
    ) -> None:

        self.client.setex(
            self._key(query),
            self.ttl_seconds,
            json.dumps(
                value,
                ensure_ascii=False,
            ),
        )
