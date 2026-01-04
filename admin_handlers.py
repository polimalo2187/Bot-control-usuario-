"""
Funciones del Administrador: Verificación, Registro, Modificación y Listado de Usuarios
Este módulo se integra con bot_principal.py
"""

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from pymongo import MongoClient
import datetime

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
ADMIN_ID = 123456789  # Reemplazar con el ID del administrador

# -----------------------------
# CONEXIÓN A MONGODB (Compartir la misma URI que bot_principal.py)
# -----------------------------
MONGO_URI = "mongodb://usuario:password@host:puerto/dbname"
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# -----------------------------
# VERIFICAR USUARIO POR ID
# -----------------------------
async def verificar_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Uso: /verificar <telegram_id>")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID inválido. Debe ser un número.")
        return

    user = users.find_one({"_id": user_id})
    if not user:
        await update.message.reply_text("❌ Usuario no registrado.")
        return

    info = (
        f"🟢 Usuario encontrado\n"
        f"ID: {user_id}\n"
        f"Username: @{user.get('username')}\n"
        f"Teléfono: {user.get('telefono')}\n"
        f"Nombre: {user.get('nombre')}\n"
        f"Apellido: {user.get('apellido')}\n"
        f"Plan: {user.get('plan')}\n"
        f"Grupo: {user.get('grupo')}\n"
        f"Academia: {user.get('academia')}\n"
        f"Verificado: {user.get('verificado')}"
    )
    await update.message.reply_text(info)

# -----------------------------
# REGISTRAR O ACTUALIZAR USUARIO
# -----------------------------
async def registrar_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 6:
        await update.message.reply_text(
            "Uso: /registrar <telegram_id> <nombre> <apellido> <plan> <grupo> <academia>"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID inválido. Debe ser un número.")
        return

    nombre = context.args[1]
    apellido = context.args[2]
    plan = context.args[3]
    grupo = context.args[4]
    academia = context.args[5]

    result = users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "nombre": nombre,
                "apellido": apellido,
                "plan": plan,
                "grupo": grupo,
                "academia": academia,
                "verificado": True
            }
        }
    )

    if result.matched_count == 0:
        await update.message.reply_text("❌ Usuario no existe.")
    else:
        await update.message.reply_text("✅ Usuario registrado o actualizado correctamente.")

# -----------------------------
# MODIFICAR USUARIO
# -----------------------------
async def modificar_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "Uso: /modificar <telegram_id> <campo> <nuevo_valor>\n"
            "Campos válidos: nombre, apellido, plan, grupo, academia"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID inválido. Debe ser un número.")
        return

    campo = context.args[1].lower()
    nuevo_valor = context.args[2]

    if campo not in ["nombre", "apellido", "plan", "grupo", "academia"]:
        await update.message.reply_text("Campo inválido. Usa nombre, apellido, plan, grupo o academia.")
        return

    result = users.update_one(
        {"_id": user_id},
        {"$set": {campo: nuevo_valor}}
    )

    if result.matched_count == 0:
        await update.message.reply_text("❌ Usuario no existe.")
    else:
        await update.message.reply_text(f"✅ Campo '{campo}' actualizado correctamente.")

# -----------------------------
# LISTAR TODOS LOS USUARIOS
# -----------------------------
async def listar_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    todos = users.find()
    mensaje = "📋 Lista de usuarios:\n\n"
    for u in todos:
        mensaje += (
            f"ID: {u.get('_id')} | "
            f"Username: @{u.get('username')} | "
            f"Plan: {u.get('plan')} | "
            f"Grupo: {u.get('grupo')} | "
            f"Academia: {u.get('academia')}\n"
        )

    if mensaje.strip() == "📋 Lista de usuarios:":
        mensaje += "No hay usuarios registrados."

    await update.message.reply_text(mensaje)
