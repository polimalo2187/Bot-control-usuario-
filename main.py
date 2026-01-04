"""
Archivo principal del bot que une bot_principal.py con admin_handlers.py
Registra todos los comandos de usuario y administrador
Adaptado para python-telegram-bot 20.5 y Motor (async) con MongoDB
Incluye prueba de conexión a MongoDB antes de arrancar el bot
"""

import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot_principal import start, recibir_contacto
from admin_handlers import verificar_usuario, registrar_usuario, modificar_usuario, listar_usuarios
from db import db  # Base de datos MongoDB revisada

# -----------------------------
# VARIABLES DE ENTORNO
# -----------------------------
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN no está definido en las variables de entorno")

# -----------------------------
# FUNCIONES AUXILIARES
# -----------------------------
async def test_db_connection():
    """Test de conexión a MongoDB antes de iniciar el bot."""
    try:
        await db.command("ping")
        print("✅ Conexión a MongoDB OK")
    except Exception as e:
        print("❌ Error conectando a MongoDB:", e)
        raise RuntimeError("No se puede iniciar el bot sin conexión a MongoDB")

# -----------------------------
# INICIALIZACIÓN DEL BOT
# -----------------------------
def main():
    # Test de MongoDB antes de crear la app
    asyncio.run(test_db_connection())

    # Crear la aplicación del bot
    app = ApplicationBuilder().token(TOKEN).build()

    # --- Handlers de usuario ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, recibir_contacto))

    # --- Handlers de administrador ---
    app.add_handler(CommandHandler("verificar", verificar_usuario))
    app.add_handler(CommandHandler("registrar", registrar_usuario))
    app.add_handler(CommandHandler("modificar", modificar_usuario))
    app.add_handler(CommandHandler("listar", listar_usuarios))

    print("✅ Bot listo y funcionando en la nube.")
    app.run_polling()

# -----------------------------
# ARRANQUE DEL BOT
# -----------------------------
if __name__ == "__main__":
    main()
