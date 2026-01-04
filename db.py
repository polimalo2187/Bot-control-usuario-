"""
Módulo de conexión a MongoDB para el bot de Telegram
Usa Motor (AsyncIOMotorClient) para compatibilidad con python-telegram-bot 20.5 (asyncio)
Centraliza la conexión y maneja timeout sin bloquear el event loop principal
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient

# Variables de entorno
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI no está definido en las variables de entorno")

# Conexión async a MongoDB
client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=10000)
db = client.telegram_bot  # Base de datos que usa el bot

# Colección de usuarios
users = db.users
