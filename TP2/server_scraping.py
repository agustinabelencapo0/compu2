import argparse
import asyncio
import json
import struct

import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

from typing import Any, Coroutine, Dict, Optional, Tuple, Union
from urllib.parse import urlparse

from aiohttp import web

from scraper.async_http import AsyncHttpClient
from scraper.html_parser import parse_basic_structure
from scraper.metadata_extractor import extract_meta_tags



@dataclass
class TaskRecord:
    task_id: str
    url: str
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def as_status_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "task_id": self.task_id,
            "url": self.url,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if self.error:
            payload["error"] = self.error
        if self.result and "status" in self.result:
            payload["result_status"] = self.result["status"]
        return payload


class TaskManager:
    def __init__(self) -> None:
        self._tasks: Dict[str, TaskRecord] = {}
        self._lock = asyncio.Lock()

    async def create_task(self, url: str) -> TaskRecord:
        record = TaskRecord(task_id=uuid.uuid4().hex, url=url)
        async with self._lock:
            self._tasks[record.task_id] = record
        return record

    async def get(self, task_id: str) -> Optional[TaskRecord]:
        async with self._lock:
            return self._tasks.get(task_id)

    async def set_status(self, task_id: str, status: str, *, error: Optional[str] = None) -> None:
        async with self._lock:
            record = self._tasks[task_id]
            record.status = status
            record.updated_at = datetime.now(timezone.utc)
            record.error = error

    async def set_result(self, task_id: str, result: Dict[str, Any], status: str = "completed") -> None:
        async with self._lock:
            record = self._tasks[task_id]
            record.result = result
            record.status = status
            record.error = None
            record.updated_at = datetime.now(timezone.utc)


class ResultCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._entries: Dict[str, Tuple[datetime, Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def get(self, url: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            entry = self._entries.get(url)
            if not entry:
                return None
            timestamp, data = entry
            if (datetime.now(timezone.utc) - timestamp).total_seconds() > self._ttl:
                del self._entries[url]
                return None
            return data

    async def set(self, url: str, data: Dict[str, Any]) -> None:
        async with self._lock:
            self._entries[url] = (datetime.now(timezone.utc), data)


class DomainRateLimiter:
    def __init__(self, max_requests_per_minute: int) -> None:
        self._max = max_requests_per_minute
        self._calls: Dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()
        self._period = 60.0

    async def allow(self, domain: str) -> bool:
        if self._max <= 0:
            return True
        now = datetime.now(timezone.utc).timestamp()
        async with self._lock:
            bucket = self._calls.setdefault(domain, deque())
            while bucket and now - bucket[0] > self._period:
                bucket.popleft()
            if len(bucket) >= self._max:
                return False
            bucket.append(now)
            return True


async def call_processing_server_async(proc_ip: str, proc_port: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    reader, writer = await asyncio.wait_for(asyncio.open_connection(proc_ip, proc_port), timeout=30.0)
    try:
        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        header = struct.pack("!I", len(data))
        writer.write(header + data)
        await writer.drain()

        header_bytes = await asyncio.wait_for(reader.readexactly(4), timeout=30.0)
        (length,) = struct.unpack("!I", header_bytes)
        if length <= 0 or length > 100_000_000:
            raise ValueError(f"Tamaño de mensaje inválido: {length}")

        data_bytes = await asyncio.wait_for(reader.readexactly(length), timeout=30.0)
        return json.loads(data_bytes.decode("utf-8"))
    finally:
        writer.close()
        await writer.wait_closed()

async def process_scrape_task(app: web.Application, task_id: str, url: str) -> None:
    manager: TaskManager = app["task_manager"]
    cache: ResultCache = app["cache"]
    config = app["config"]

    try:
        await manager.set_status(task_id, "scraping")
        async with AsyncHttpClient(timeout=30, max_connections_per_host=config["workers"]) as client:
            html = await client.fetch_text(url)


        basic = parse_basic_structure(html, base_url=url)
        meta = extract_meta_tags(html)

        scraping_data = {
            "title": basic["title"],
            "links": basic["links"],
            "meta_tags": meta,
            "structure": basic["structure"],
            "images_count": basic["images_count"],
        }


        image_urls = basic.get("image_urls", [])
        processing_payload = {
            "url": url,
            "tasks": {
                "screenshot": True,
                "performance": True,
                "thumbnails": True,

                "tech_stack": True,
                "seo": True,
                "structured_data": True,
                "accessibility": True,
            },
            "image_urls": image_urls[: config.get("image_limit", 3)],
            "html": html,
            "scraping_data": scraping_data,
        }

        await manager.set_status(task_id, "processing")
        try:
            processing_response = await call_processing_server_async(
                config["proc_ip"], config["proc_port"], processing_payload
            )
        except Exception as exc:
            processing_response = {
                "status": "error", 
                "processing_data": {}, 

                "error": f"{type(exc).__name__}: {exc}",
            }

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        result = {
            "url": url,
            "timestamp": now,
            "scraping_data": scraping_data,
            "processing_data": processing_response.get("processing_data", {}),
            "status": "success" if processing_response.get("status") == "success" else "partial",
        }
        if "error" in processing_response:

            result["processing_error"] = processing_response["error"]


        await manager.set_result(task_id, result, status="completed")
        await cache.set(url, result)
    except asyncio.TimeoutError:

        await manager.set_status(task_id, "failed", error="Timeout")
    except Exception as exc:  # pylint: disable=broad-except
        await manager.set_status(task_id, "failed", error=str(exc))


async def handle_scrape(request: web.Request) -> web.Response:
    data = await _extract_url(request)
    if isinstance(data, web.Response):
        return data
    url = data

    domain = urlparse(url).hostname
    if not domain:
        return web.json_response({"status": "error", "error": "URL inválida"}, status=400)

    rate_limiter: DomainRateLimiter = request.app["rate_limiter"]
    allowed = await rate_limiter.allow(domain)
    if not allowed:
        return web.json_response(
            {"status": "error", "error": "Rate limit excedido para el dominio"},
            status=429,
        )

    cache: ResultCache = request.app["cache"]
    manager: TaskManager = request.app["task_manager"]

    record = await manager.create_task(url)

    cached = await cache.get(url)
    if cached:
        await manager.set_result(record.task_id, cached, status="completed")
        return web.json_response({"task_id": record.task_id, "status": "completed", "cached": True})

    schedule_background_task(request.app, process_scrape_task(request.app, record.task_id, url))
    return web.json_response({"task_id": record.task_id, "status": record.status}, status=202)


async def handle_status(request: web.Request) -> web.Response:
    task_id = request.match_info.get("task_id", "")
    manager: TaskManager = request.app["task_manager"]
    record = await manager.get(task_id)
    if not record:
        return web.json_response({"status": "error", "error": "task_id inexistente"}, status=404)
    return web.json_response(record.as_status_payload())


async def handle_result(request: web.Request) -> web.Response:
    task_id = request.match_info.get("task_id", "")
    manager: TaskManager = request.app["task_manager"]
    record = await manager.get(task_id)
    if not record:
        return web.json_response({"status": "error", "error": "task_id inexistente"}, status=404)
    if record.status != "completed" or not record.result:
        if record.status == "failed":
            return web.json_response(
                {"status": "error", "error": record.error or "Tarea fallida"},
                status=500,
            )
        return web.json_response(
            {"status": "pending", "message": "La tarea aún no finalizó"},
            status=202,
        )
    payload = dict(record.result)
    payload["task_id"] = task_id
    return web.json_response(payload)


def schedule_background_task(app: web.Application, coro: Coroutine[Any, Any, Any]) -> None:
    task = asyncio.create_task(coro)
    running = app["running_tasks"]
    running.add(task)
    task.add_done_callback(lambda t: running.discard(t))


async def _extract_url(request: web.Request) -> Union[str, web.Response]:
    if request.method == "GET":
        url = request.query.get("url")
    else:
        try:
            payload = await request.json()
        except Exception:  # pylint: disable=broad-except
            return web.json_response({"status": "error", "error": "Body inválido"}, status=400)
        url = payload.get("url") if isinstance(payload, dict) else None
    if not url:
        return web.json_response({"status": "error", "error": "Missing url param"}, status=400)
    return url


def build_app(
    listen_ip: str,
    listen_port: int,
    proc_ip: str,
    proc_port: int,
    workers: int,
    rate_limit: int,
    cache_ttl: int,
) -> web.Application:
    app = web.Application()

    app["config"] = {
        "listen_ip": listen_ip,
        "listen_port": listen_port,
        "proc_ip": proc_ip,
        "proc_port": proc_port,
        "workers": workers,
        "image_limit": 3,
    }
    app["task_manager"] = TaskManager()
    app["cache"] = ResultCache(ttl_seconds=cache_ttl)
    app["rate_limiter"] = DomainRateLimiter(max_requests_per_minute=rate_limit)
    app["running_tasks"] = set()

    app.router.add_get("/scrape", handle_scrape)

    app.router.add_post("/scrape", handle_scrape)
    app.router.add_get("/status/{task_id}", handle_status)
    app.router.add_get("/result/{task_id}", handle_result)
    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Servidor de Scraping Web Asíncrono")
    parser.add_argument("-i", "--ip", required=True, help="Dirección de escucha (IPv4/IPv6)")
    parser.add_argument("-p", "--port", required=True, type=int, help="Puerto de escucha")

    parser.add_argument("-w", "--workers", default=4, type=int, help="Número de workers HTTP")
    parser.add_argument("--proc-ip", required=True, help="IP del servidor de procesamiento")
    parser.add_argument("--proc-port", required=True, type=int, help="Puerto del servidor de procesamiento")

    parser.add_argument(
        "--rate-limit",
        type=int,
        default=5,
        help="Máximo de solicitudes por dominio por minuto (default: 5)",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=3600,
        help="Tiempo de vida del cache en segundos (default: 3600)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    app = build_app(
        listen_ip=args.ip,
        listen_port=args.port,
        proc_ip=args.proc_ip,
        proc_port=args.proc_port,
        workers=args.workers,
        rate_limit=args.rate_limit,
        cache_ttl=args.cache_ttl,
    )
    web.run_app(app, host=args.ip, port=args.port)


if __name__ == "__main__":
    main()


