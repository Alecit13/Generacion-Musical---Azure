import asyncio
import json
import websockets

clientes_conectados = set()   # sockets de los navegadores conectados ahora mismo


async def manejar_cliente(websocket):
    """Registra un navegador al conectarse y lo quita al desconectarse (por cualquier motivo,
    incluido un cierre con error). Lo llama websockets.serve en main.py una vez por cliente.
    Variable importante: clientes_conectados, que usa enviar_a_todos."""
    clientes_conectados.add(websocket)
    try:
        async for _ in websocket:      # no esperamos mensajes del navegador; solo mantenemos la conexión
            pass
    except websockets.exceptions.ConnectionClosed:
        pass                           # desconexión normal o por error: no es un problema
    finally:
        clientes_conectados.discard(websocket)


async def enviar_a_todos(datos):
    """Envía un diccionario (como JSON) a todos los navegadores conectados.
    Lo llama bucle_kinect en cada ciclo. Si un cliente falla, se descarta en silencio
    y el bucle de la Kinect SIGUE funcionando (antes la excepción apagaba todo)."""
    if not clientes_conectados:
        return
    mensaje = json.dumps(datos)
    clientes = list(clientes_conectados)          # copia: el set puede cambiar durante el envío
    resultados = await asyncio.gather(*(ws.send(mensaje) for ws in clientes),
                                      return_exceptions=True)
    for ws, r in zip(clientes, resultados):
        if isinstance(r, Exception):
            clientes_conectados.discard(ws)