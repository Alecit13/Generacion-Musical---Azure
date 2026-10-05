import asyncio
import json

clientes_conectados = set()

async def manejar_cliente(websocket):
    clientes_conectados.add(websocket)
    try:
        async for _ in websocket:
            pass  # no necesitamos recibir nada del navegador, solo enviarle datos
    finally:
        clientes_conectados.discard(websocket)

async def enviar_a_todos(datos: dict):
    if clientes_conectados:
        mensaje = json.dumps(datos)
        await asyncio.gather(*(ws.send(mensaje) for ws in clientes_conectados))