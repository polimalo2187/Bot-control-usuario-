"""
Bot de Gestión de Usuarios, Planes, Grupos y Academias
Funciona en la nube con MongoDB (Anubis)
Roles: Usuario (registro mínimo) y Administrador (control total)
"""

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
import datetime

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
TOKEN = "TU_BOT_TOKEN"
ADMIN_ID = 123456789  # Reemplazar con el ID del administrador
MONGO_URI = "mongodb://usuario:password@host:puerto/dbname"  # URI de conexión a MongoDB

# -----------------------------
# CONEXIÓN A MONGODB
# -----------------------------
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# -----------------------------
# HANDLER / START (Usuario)
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Registrar usuario si no existe
    users.update_one(
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

    # Botón para compartir teléfono
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
# HANDLER PARA RECIBIR TELEFONO
# -----------------------------
async def recibir_contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact

    if contact.user_id != update.effective_user.id:
        await update.message.reply_text("Contacto inválido.")
        return

    users.update_one(
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

    # Nota: los handlers de administrador se agregarán en próximos archivos

    print("Bot iniciado y listo para funcionar en la nube.")
    app.run_polling()

if __name__ == "__main__":
    main()
