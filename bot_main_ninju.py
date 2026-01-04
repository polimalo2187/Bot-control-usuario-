"""
Archivo principal del bot que une bot_principal.py con admin_handlers.py
Registra todos los comandos de usuario y administrador
Diseñado para correr en la nube con MongoDB (Anubis)
"""

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot_principal import start, recibir_contacto
from admin_handlers import verificar_usuario, registrar_usuario, modificar_usuario, listar_usuarios

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
TOKEN = "TU_BOT_TOKEN"

# -----------------------------
# INICIALIZACIÓN DEL BOT
# -----------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # --- Handlers de usuario ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, recibir_contacto))

    # --- Handlers de administrador ---
    app.add_handler(CommandHandler("verificar", verificar_usuario))
    app.add_handler(CommandHandler("registrar", registrar_usuario))
    app.add_handler(CommandHandler("modificar", modificar_usuario))
    app.add_handler(CommandHandler("listar", listar_usuarios))

    print("Bot listo y funcionando en la nube.")
    app.run_polling()

if __name__ == "__main__":
    main()
