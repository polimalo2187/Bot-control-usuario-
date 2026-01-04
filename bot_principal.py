"""
Bot de Gestión de Usuarios: Registro y manejo de información
Adaptado para python-telegram-bot 20.5 y Motor (async) con MongoDB
"""

import datetime
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from db import users  # Importa la colección centralizada

# -----------------------------
# CONFIGURACIÓN (VARIABLES DE ENTORNO)
# -----------------------------
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN no está definido en las variables de entorno")

# -----------------------------
# HANDLER / START (Usuario)
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Registrar usuario si no existe
    await users.update_one(
        {"_id": user.id},
        {
            "$setOnInsert": {
                "username": user.username,
                "telefono": None,
                "nombre": None,
                "apellido": None,
                "verificado": False,
                "plan": None,
                "grupo": None,
                "academia": None,
                "fecha_registro": datetime.datetime.utcnow()
            }
        },
        upsert=True
    )

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Compartir teléfono", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        "Bienvenido al sistema de registro de usuarios.\n"
        "Por favor, comparte tu número de teléfono para completar tu registro.",
        reply_markup=keyboard
    )

# -----------------------------
# HANDLER PARA RECIBIR TELÉFONO
# -----------------------------
async def recibir_contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact

    if contact.user_id != update.effective_user.id:
        await update.message.reply_text("❌ Contacto inválido.")
        return

    await users.update_one(
        {"_id": contact.user_id},
        {"$set": {"telefono": contact.phone_number}}
    )

    await update.message.reply_text("✅ Registro completado. Ahora eres parte del sistema.")

# -----------------------------
# INICIALIZACIÓN DEL BOT
# -----------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers de usuario
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, recibir_contacto))

    print("✅ Bot iniciado correctamente y conectado a MongoDB.")
    app.run_polling()

if __name__ == "__main__":
    main()
