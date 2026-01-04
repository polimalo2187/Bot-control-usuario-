"""
Módulo de conexión a MongoDB para el bot de Telegram
Usa Motor (AsyncIOMotorClient) para compatibilidad con python-telegram-bot 20.5 (asyncio)
Centraliza la conexión y maneja errores y timeout
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError

# -----------------------------
# VARIABLES DE ENTORNO
# -----------------------------
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI no está definido en las variables de entorno")

# -----------------------------
# CONEXIÓN ASYNC A MONGODB
# -----------------------------
try:
    client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.telegram_bot
    # Test de conexión (async)
    import asyncio
    async def test_connection():
        try:
            await db.command("ping")
            print("✅ Conexión a MongoDB establecida correctamente")
        except ServerSelectionTimeoutError as e:
            raise RuntimeError(f"❌ No se pudo conectar a MongoDB: {e}")

    asyncio.get_event_loop().run_until_complete(test_connection())
except (ConfigurationError, ServerSelectionTimeoutError) as e:
    raise RuntimeError(f"❌ Error en la configuración de MongoDB: {e}")

# -----------------------------
# COLECCIÓN DE USUARIOS
# -----------------------------
users = db.users
