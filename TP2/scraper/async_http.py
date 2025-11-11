import asyncio
from typing import Optional

import aiohttp


DEFAULT_TIMEOUT_SECS = 30


class AsyncHttpClient:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT_SECS, max_connections_per_host: int = 8) -> None:
        timeout_cfg = aiohttp.ClientTimeout(total=timeout)
        connector = aiohttp.TCPConnector(limit_per_host=max_connections_per_host)
        self._session = aiohttp.ClientSession(timeout=timeout_cfg, connector=connector)

    async def close(self) -> None:
        await self._session.close()

    async def fetch_text(self, url: str) -> str:
        async with self._session.get(url, allow_redirects=True) as resp:
            resp.raise_for_status()
            return await resp.text(errors="ignore")

    async def fetch_bytes(self, url: str) -> bytes:
        async with self._session.get(url, allow_redirects=True) as resp:
            resp.raise_for_status()
            return await resp.read()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> Optional[bool]:
        await self.close()
        return None


async def fetch_html_with_timeout(url: str, timeout: int = DEFAULT_TIMEOUT_SECS) -> str:
    async with AsyncHttpClient(timeout=timeout) as client:
        return await client.fetch_text(url)

