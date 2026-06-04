# backend/api/websocket.py
"""WebSocket para atualização em tempo real dos timers."""

from __future__ import annotations
import asyncio
import json
from typing import List, Set
from fastapi import WebSocket, WebSocketDisconnect

from controller import Controller
from model import Categories


class ConnectionManager:
    """Gerencia conexões WebSocket."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.controller: Controller = None

    def set_controller(self, ctrl: Controller) -> None:
        """Define o controller."""
        self.controller = ctrl

    async def connect(self, websocket: WebSocket) -> None:
        """Aceita nova conexão."""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove conexão."""
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        """Envia mensagem para todas as conexões."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Remove conexões mortas
        self.active_connections -= disconnected

    async def broadcast_timers(self) -> None:
        """Envia atualização de todos os timers."""
        if not self.controller or not self.active_connections:
            return

        demands = self.controller.get_all_demands()
        timers = {}

        for d in demands:
            timers[d.id] = {
                "id": d.id,
                "status": d.status,
                "current_elapsed_time": d.get_current_elapsed_time(),
                "accumulated_time": d.accumulated_time,
            }

        await self.broadcast({"type": "timers", "data": timers})


manager = ConnectionManager()


async def timer_broadcast_loop():
    """Loop que envia atualizações de timer a cada segundo."""
    while True:
        await manager.broadcast_timers()
        await asyncio.sleep(1)


async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para conexão de clientes."""
    await manager.connect(websocket)
    try:
        while True:
            # Mantém a conexão aberta, aguardando mensagens do cliente
            data = await websocket.receive_text()
            # Pode processar comandos do cliente aqui se necessário
    except WebSocketDisconnect:
        manager.disconnect(websocket)
