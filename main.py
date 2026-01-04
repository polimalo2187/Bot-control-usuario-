import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot_principal import start, recibir_contacto
from admin_handlers import verificar_usuario, registrar_usuario, modificar_usuario, listar_usuarios
from db import db

# Token
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN no está definido en las variables de entorno")

# Test de conexión a MongoDB
async def test_db_connection():
    try:
        await db.command("ping")
        print("✅ Conexión a MongoDB OK")
    except Exception as e:
        print("❌ Error conectando a MongoDB:", e)
        raise RuntimeError("No se puede iniciar el bot sin conexión a MongoDB")

def main():
    asyncio.run(test_db_connection())

    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers de usuario
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, recibir_contacto))

    # Handlers de administrador
    app.add_handler(CommandHandler("verificar", verificar_usuario))
    app.add_handler(CommandHandler("registrar", registrar_usuario))
    app.add_handler(CommandHandler("modificar", modificar_usuario))
    app.add_handler(CommandHandler("listar", listar_usuarios))

    print("✅ Bot listo y funcionando en la nube.")
    app.run_polling()

if __name__ == "__main__":
    main()
