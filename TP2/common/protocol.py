import json
import socket
import struct
from typing import Any, Dict

HEADER_STRUCT = struct.Struct("!I")  # longitud del mensaje (uint32 big-endian)


def send_message(sock: socket.socket, payload: Dict[str, Any]) -> None:
    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    header = HEADER_STRUCT.pack(len(data))
    sock.sendall(header + data)
    # Asegurar que los datos se envíen antes de cerrar
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except Exception:
        pass


def recv_all(sock: socket.socket, nbytes: int) -> bytes:
    chunks: list[bytes] = []
    remaining = nbytes
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("Conexión cerrada inesperadamente")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_message(sock: socket.socket) -> Dict[str, Any]:
    header_bytes = recv_all(sock, HEADER_STRUCT.size)
    (length,) = HEADER_STRUCT.unpack(header_bytes)
    if length <= 0 or length > 1_000_000_000:
        raise ValueError("Tamaño de mensaje inválido")
    data = recv_all(sock, length)
    return json.loads(data.decode("utf-8"))

