#!/bin/bash
# Script de build para produção (Render)

set -e

echo "=== Instalando dependências do backend ==="
cd backend
pip install -r requirements.txt

echo "=== Instalando dependências do frontend ==="
cd ../frontend
npm install

echo "=== Build do frontend ==="
npm run build

echo "=== Copiando frontend para backend/static ==="
rm -rf ../backend/static
cp -r dist ../backend/static

echo "=== Build completo! ==="
