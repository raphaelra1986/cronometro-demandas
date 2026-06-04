#!/usr/bin/env python
"""Script para iniciar o backend e frontend."""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"


def check_npm():
    """Verifica se npm está instalado."""
    try:
        subprocess.run(["npm", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_frontend_deps():
    """Instala dependências do frontend se necessário."""
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("Instalando dependências do frontend...")
        subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, check=True)


def main():
    print("=" * 50)
    print("Cronômetro de Demandas - Web App")
    print("=" * 50)

    # Verificar npm
    if not check_npm():
        print("\nERRO: npm não encontrado!")
        print("Por favor, instale o Node.js: https://nodejs.org/")
        sys.exit(1)

    # Instalar deps do frontend
    try:
        install_frontend_deps()
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar dependências: {e}")
        sys.exit(1)

    # Iniciar backend
    print("\nIniciando backend (FastAPI)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd=BACKEND_DIR
    )

    # Aguardar backend iniciar
    time.sleep(2)

    # Iniciar frontend
    print("Iniciando frontend (Vue)...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR
    )

    # Aguardar e abrir navegador
    time.sleep(3)
    print("\n" + "=" * 50)
    print("Aplicação iniciada!")
    print("Backend:  http://localhost:8000")
    print("Frontend: http://localhost:5173")
    print("API Docs: http://localhost:8000/docs")
    print("=" * 50)
    print("\nPressione Ctrl+C para encerrar.\n")

    webbrowser.open("http://localhost:5173")

    try:
        # Aguardar processos
        backend_process.wait()
    except KeyboardInterrupt:
        print("\nEncerrando...")
        backend_process.terminate()
        frontend_process.terminate()
        print("Aplicação encerrada.")


if __name__ == "__main__":
    main()
