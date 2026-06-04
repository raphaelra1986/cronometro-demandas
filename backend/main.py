# backend/main.py
"""Aplicação FastAPI principal."""

from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from controller import Controller
from database import DatabaseManager
from api.routes import router, set_controller
from api.websocket import manager, websocket_endpoint, timer_broadcast_loop
from logger import log_operation, log_info


# Lifespan para inicialização e finalização
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    log_operation("Backend starting")

    # Criar backup na inicialização
    db = DatabaseManager()
    backup_path = db.create_backup()
    if backup_path:
        log_operation("Backup created", f"Path: {backup_path}")

    # Inicializar controller
    controller = Controller()
    set_controller(controller)
    manager.set_controller(controller)

    # Iniciar loop de broadcast de timers
    timer_task = asyncio.create_task(timer_broadcast_loop())

    log_info("Backend ready")

    yield

    # Cleanup
    timer_task.cancel()
    try:
        await timer_task
    except asyncio.CancelledError:
        pass

    controller.close()
    log_operation("Backend shutdown")


# Criar aplicação
app = FastAPI(
    title="Cronômetro de Demandas",
    description="API para gerenciamento de demandas com cronômetro",
    version="2.0.0",
    lifespan=lifespan,
)

# Configurar CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rotas da API
app.include_router(router)


# WebSocket endpoint
@app.websocket("/ws/timers")
async def ws_timers(websocket: WebSocket):
    """WebSocket para atualização em tempo real dos timers."""
    await websocket_endpoint(websocket)


# Servir frontend em produção
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "static")

# Verificar se existe o diretório de frontend buildado
if os.path.exists(FRONTEND_DIR) and os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
    # Servir assets estáticos
    if os.path.exists(os.path.join(FRONTEND_DIR, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/{path:path}")
    async def serve_frontend_paths(path: str):
        # Ignorar rotas de API
        if path.startswith("api/") or path.startswith("ws/"):
            return {"detail": "Not Found"}
        file_path = os.path.join(FRONTEND_DIR, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
