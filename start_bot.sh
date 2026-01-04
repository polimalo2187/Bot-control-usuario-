#!/bin/bash
# Script para arrancar bot versión 2 en Raiwan con MongoDB

# --- Variables de entorno ---
export BOT_TOKEN="TU_BOT_TOKEN"
export ADMIN_ID="123456789"
export MONGO_URI="mongodb+srv://Carlos2187:21872187Crp@controlusuario.oszzrpp.mongodb.net/telegram_bot?appName=Controlusuario"

# --- Instalar dependencias ---
pip install --upgrade pip
pip install python-telegram-bot==20.5 motor==3.1.1

# --- Arrancar el bot en segundo plano ---
nohup python3 main.py &
echo "✅ Bot arrancado en segundo plano"
