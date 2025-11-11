import argparse
import socketserver
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, List, Tuple

from socketserver import ThreadingMixIn

from common.protocol import recv_message, send_message
from common.serialization import bytes_to_base64
from processor.advanced import (
    analyze_accessibility,
    detect_technologies,
    evaluate_seo,
    extract_structured_data,
)
from processor.image_processor import generate_thumbnails
from processor.performance import analyze_performance
from processor.screenshot import take_screenshot


def _encode_thumbnails(thumbs: List[bytes]) -> List[str]:
    encoded: List[str] = []
    for thumb in thumbs:
        encoded_thumb = bytes_to_base64(thumb)
        if encoded_thumb is not None:
            encoded.append(encoded_thumb)
    return encoded


def process_tasks(
    url: str,
    tasks: Dict[str, Any],
    image_urls: List[str],
    html: str,
    scraping_data: Dict[str, Any],
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "screenshot": None,
        "performance": None,
        "thumbnails": [],
        "tech_stack": [],
        "seo": {},
        "structured_data": [],
        "accessibility": {},
    }

    if tasks.get("screenshot"):
        try:
            png = take_screenshot(url)
            out["screenshot"] = bytes_to_base64(png)
        except Exception:
            out["screenshot"] = None

    if tasks.get("performance"):
        try:
            out["performance"] = analyze_performance(url)
        except Exception:
            out["performance"] = None

    if tasks.get("thumbnails") and image_urls:
        try:
            thumbs = generate_thumbnails(image_urls)
            out["thumbnails"] = _encode_thumbnails(thumbs)
        except Exception:
            out["thumbnails"] = []

    if tasks.get("tech_stack") and html:
        try:
            out["tech_stack"] = detect_technologies(html)
        except Exception:
            out["tech_stack"] = []

    if tasks.get("seo") and html:
        try:
            out["seo"] = evaluate_seo(html, scraping_data)
        except Exception:
            out["seo"] = {}

    if tasks.get("structured_data") and html:
        try:
            out["structured_data"] = extract_structured_data(html)
        except Exception:
            out["structured_data"] = []

    if tasks.get("accessibility") and html:
        try:
            out["accessibility"] = analyze_accessibility(html)
        except Exception:
            out["accessibility"] = {}

    return out


class ProcessingTCPHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        try:
            payload = recv_message(self.request)
            url = payload.get("url")
            tasks = payload.get("tasks", {})
            image_urls = payload.get("image_urls", [])
            html = payload.get("html", "")
            scraping_data = payload.get("scraping_data", {})

            if not url:
                resp = {"status": "error", "error": "missing url"}
                send_message(self.request, resp)
                return

            future = self.server.pool.submit(  # type: ignore[attr-defined]
                process_tasks, url, tasks, image_urls, html, scraping_data
            )
            result = future.result()

            resp = {
                "status": "success",
                "processing_data": result,
            }
            send_message(self.request, resp)
        except Exception as e:
            send_message(self.request, {"status": "error", "error": str(e)})


class ProcessingTCPServer(ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address: Tuple[str, int], RequestHandlerClass, processes: int):
        super().__init__(server_address, RequestHandlerClass)
        self.pool = ProcessPoolExecutor(max_workers=processes)

    def server_close(self) -> None:
        self.pool.shutdown(wait=True, cancel_futures=True)
        super().server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Servidor de Procesamiento Distribuido")
    parser.add_argument("-i", "--ip", required=True, help="Dirección de escucha")
    parser.add_argument("-p", "--port", required=True, type=int, help="Puerto de escucha")
    parser.add_argument("-n", "--processes", type=int, default=None, help="Número de procesos en el pool")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    processes = args.processes
    if processes is None or processes <= 0:
        import os

        processes = max(1, os.cpu_count() or 1)

    with ProcessingTCPServer((args.ip, args.port), ProcessingTCPHandler, processes=processes) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()

