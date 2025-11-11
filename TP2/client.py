import argparse
import asyncio
import json
from typing import Any, Dict

import aiohttp


async def submit_task(session: aiohttp.ClientSession, base_url: str, url: str) -> Dict[str, Any]:
    endpoint = f"{base_url}/scrape"
    async with session.post(endpoint, json={"url": url}) as resp:
        resp.raise_for_status()
        return await resp.json()


async def wait_for_completion(
    session: aiohttp.ClientSession,
    base_url: str,
    task_id: str,
    interval: float,
    timeout: float,
) -> Dict[str, Any]:
    status_endpoint = f"{base_url}/status/{task_id}"
    result_endpoint = f"{base_url}/result/{task_id}"
    deadline = asyncio.get_event_loop().time() + timeout

    while True:
        async with session.get(status_endpoint) as resp:
            if resp.status == 404:
                raise RuntimeError("task_id inexistente")
            status_payload = await resp.json()

        status = status_payload.get("status")
        if status == "completed":
            async with session.get(result_endpoint) as resp:
                resp.raise_for_status()
                return await resp.json()
        if status == "failed":
            error = status_payload.get("error", "tarea fallida")
            raise RuntimeError(error)

        if asyncio.get_event_loop().time() >= deadline:
            raise TimeoutError("Tiempo de espera agotado esperando resultado")

        await asyncio.sleep(interval)


async def main_async(ip: str, port: int, url: str, interval: float, timeout: float, wait: bool) -> None:
    base_url = f"http://{ip}:{port}"
    timeout_cfg = aiohttp.ClientTimeout(total=timeout + 30)
    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        submission = await submit_task(session, base_url, url)
        if submission.get("status") == "completed" and submission.get("cached"):
            async with session.get(f"{base_url}/result/{submission['task_id']}") as resp:
                resp.raise_for_status()
                data = await resp.json()
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return

        if not wait:
            print(json.dumps(submission, indent=2, ensure_ascii=False))
            return

        data = await wait_for_completion(session, base_url, submission["task_id"], interval, timeout)
        print(json.dumps(data, indent=2, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cliente de prueba TP2")
    parser.add_argument("-i", "--ip", required=True)
    parser.add_argument("-p", "--port", required=True, type=int)
    parser.add_argument("-u", "--url", required=True)
    parser.add_argument("--interval", type=float, default=1.5, help="Intervalo de pooling en segundos")
    parser.add_argument("--timeout", type=float, default=120.0, help="Tiempo máximo de espera en segundos")
    parser.add_argument("--no-wait", action="store_true", help="No esperar a que la tarea finalice")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    wait = not args.no_wait
    asyncio.run(main_async(args.ip, args.port, args.url, args.interval, args.timeout, wait))


if __name__ == "__main__":
    main()

