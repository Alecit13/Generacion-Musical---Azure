import asyncio
import json

clientes_conectados = set()


async def manejar_cliente(websocket):
    """Registra un navegador mientras esté conectado y lo quita al desconectarse.
    Relación: main.py lo pasa a websockets.serve; enviar_a_todos usa el conjunto que este mantiene.
    Variable: `clientes_conectados` (conjunto de conexiones abiertas)."""
    clientes_conectados.add(websocket)
    try:
        async for _ in websocket:
            pass  # no necesitamos recibir nada del navegador, solo enviarle datos
    finally:
        clientes_conectados.discard(websocket)


async def enviar_a_todos(datos: dict):
    """Envía el estado musical a todos los navegadores conectados.
    Si un navegador se cerró justo en este instante, su envío falla: se descarta ESE cliente
    y el programa sigue (antes, el error subía hasta el ciclo principal y podía detener Python).
    Variables: `clientes` (copia de la lista, porque el conjunto puede cambiar mientras se envía)."""
    if not clientes_conectados:
        return
    mensaje = json.dumps(datos)
    clientes = list(clientes_conectados)
    resultados = await asyncio.gather(*(ws.send(mensaje) for ws in clientes), return_exceptions=True)
    for ws, r in zip(clientes, resultados):
        if isinstance(r, Exception):
            clientes_conectados.discard(ws)