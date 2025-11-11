import asyncio
import struct
import json

async def test():
    r, w = await asyncio.open_connection('127.0.0.1', 9001)
    try:
        payload = {'url': 'https://example.com', 'tasks': {'performance': True}}
        data = json.dumps(payload).encode('utf-8')
        w.write(struct.pack('!I', len(data)) + data)
        await w.drain()
        
        h = await r.readexactly(4)
        l = struct.unpack('!I', h)[0]
        print(f'Length recibido: {l}, hex header: {h.hex()}, como texto: {h}')
        if l > 1000000:
            print(f'ERROR: Tamaño inválido! Parece que recibimos: {h}')
    finally:
        w.close()
        await w.wait_closed()

asyncio.run(test())

