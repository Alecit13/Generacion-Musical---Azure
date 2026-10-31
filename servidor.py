import asyncio
import json

clientes_conectados = set()
al_recibir = None   # función (str) -> None que main.py asigna para procesar lo que envía el navegador (latencias)


async def manejar_cliente(websocket):
    """Registra un navegador mientras esté conectado y lo quita al desconectarse.
    Cada mensaje que llegue del navegador se pasa a `al_recibir` (si main.py la asignó); un mensaje
    malformado se avisa y se ignora, nunca cierra la conexión.
    Relación: main.py lo pasa a websockets.serve; enviar_a_todos usa el conjunto que este mantiene.
    Variables: `clientes_conectados` (conexiones abiertas), `al_recibir` (callback de main.py)."""
    clientes_conectados.add(websocket)
    try:
        async for mensaje in websocket:
            if al_recibir is not None:
                try:
                    al_recibir(mensaje)
                except Exception as e:
                    print(f"[servidor] mensaje del navegador ignorado: {e!r}")
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