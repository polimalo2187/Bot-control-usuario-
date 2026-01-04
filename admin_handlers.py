"""
Funciones del Administrador: Verificación, Registro, Modificación y Listado de Usuarios
Adaptado para python-telegram-bot 20.5 y Motor (async) con MongoDB
"""

import os
from telegram import Update
from telegram.ext import ContextTypes
from db import users  # Colección centralizada

# Configuración
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Verificar usuario por ID
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

    user = await users.find_one({"_id": user_id})
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

# Registrar o actualizar usuario
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

    nombre, apellido, plan, grupo, academia = context.args[1:6]

    result = await users.update_one(
        {"_id": user_id},
        {"$set": {"nombre": nombre, "apellido": apellido, "plan": plan, "grupo": grupo, "academia": academia, "verificado": True}}
    )

    if result.matched_count == 0:
        await update.message.reply_text("❌ Usuario no existe.")
    else:
        await update.message.reply_text("✅ Usuario registrado o actualizado correctamente.")

# Modificar usuario
async def modificar_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "Uso: /modificar <telegram_id> <campo> <nuevo_valor>\nCampos válidos: nombre, apellido, plan, grupo, academia"
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

    result = await users.update_one({"_id": user_id}, {"$set": {campo: nuevo_valor}})
    if result.matched_count == 0:
        await update.message.reply_text("❌ Usuario no existe.")
    else:
        await update.message.reply_text(f"✅ Campo '{campo}' actualizado correctamente.")

# Listar todos los usuarios
async def listar_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor = users.find()
    mensaje = "📋 Lista de usuarios:\n\n"
    async for u in cursor:
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
