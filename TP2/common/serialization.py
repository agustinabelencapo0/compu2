import base64
from typing import Optional


def bytes_to_base64(data: Optional[bytes]) -> Optional[str]:
    if data is None:
        return None
    return base64.b64encode(data).decode("ascii")


def base64_to_bytes(data: Optional[str]) -> Optional[bytes]:
    if data is None:
        return None
    return base64.b64decode(data)

