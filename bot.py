import os
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS, POLLING
from database import users

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("telegram_admin_bot")

bot = telebot.TeleBot(BOT_TOKEN)

# -------------------------
# Estado por admin (thread-safe)
# -------------------------
admin_states_lock = threading.Lock()
admin_states: Dict[int, Dict[str, Any]] = {}  # admin_id -> state dict

def set_admin_state(admin_id: int, data: Dict[str, Any]):
    with admin_states_lock:
        admin_states[admin_id] = data

def get_admin_state(admin_id: int) -> Optional[Dict[str, Any]]:
    with admin_states_lock:
        return admin_states.get(admin_id)

def clear_admin_state(admin_id: int):
    with admin_states_lock:
        admin_states.pop(admin_id, None)

# -------------------------
# Constantes y validaciones
# -------------------------
VALID_PLANS = {"Free", "Plus", "Premium"}
VALID_GROUPS = {"Grupo Free", "Grupo Plus", "Grupo Premium"}
VALID_ACADEMIES = {"Academia Free", "Academia Plus", "Academia Premium"}

PAGE_SIZE = 10

# -------------------------
# Utilidades
# -------------------------
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def get_user(telegram_id: int) -> Optional[dict]:
    return users.find_one({"telegram_id": telegram_id})

def safe_int(text: str) -> Optional[int]:
    try:
        return int(text.strip())
    except Exception:
        return None

# -------------------------
# Handlers: Start y registro de contacto
# -------------------------
@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    try:
        telegram_id = message.from_user.id
        username = message.from_user.username or ""
        chat_id = message.chat.id

        if get_user(telegram_id):
            bot.send_message(chat_id, "✅ Ya estás registrado.")
            return

        users.insert_one({
            "telegram_id": telegram_id,
            "username": username,
            "telefono": None,
            "fecha_registro": datetime.utcnow(),
            "nombre": None,
            "apellido": None,
            "plan": None,
            "grupo": None,
            "academia": None
        })

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(types.KeyboardButton("📱 Compartir teléfono", request_contact=True))

        bot.send_message(
            chat_id,
            "Por favor comparte tu número de teléfono para completar el registro.",
            reply_markup=kb
        )
        logger.info("Nuevo usuario iniciado: %s (@%s)", telegram_id, username)
    except Exception:
        logger.exception("Error en /start")
        bot.send_message(message.chat.id, "Ha ocurrido un error; inténtalo de nuevo más tarde.")

@bot.message_handler(content_types=["contact"])
def save_phone(message: telebot.types.Message):
    try:
        # Validar que el contacto sea del mismo usuario
        if not message.contact:
            return
        contact_user_id = getattr(message.contact, "user_id", None)
        sender_id = message.from_user.id

        if contact_user_id is None or contact_user_id != sender_id:
            # Ignorar contactos que no pertenezcan al emisor
            logger.warning("Contacto recibido que no coincide con el usuario: sender=%s contact_user=%s", sender_id, contact_user_id)
            return

        # Asegurar que el usuario existe en DB
        if not get_user(sender_id):
            bot.send_message(message.chat.id, "Primero debes presionar /start para iniciar el registro.")
            return

        phone = message.contact.phone_number
        users.update_one({"telegram_id": sender_id}, {"$set": {"telefono": phone}})
        bot.send_message(message.chat.id, "✅ Registro completado correctamente.", reply_markup=types.ReplyKeyboardRemove())
        logger.info("Teléfono guardado para %s: %s", sender_id, phone)
    except Exception:
        logger.exception("Error al guardar teléfono")
        bot.send_message(message.chat.id, "Ha ocurrido un error al completar el registro.")

# -------------------------
# Menú Admin (comando /admin)
# -------------------------
@bot.message_handler(commands=["admin"])
def admin_menu(message: telebot.types.Message):
    try:
        user_id = message.from_user.id
        if not is_admin(user_id):
            logger.warning("Acceso no autorizado al panel admin: %s", user_id)
            return

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(
            "🔍 Verificar usuario",
            "📝 Registrar usuario",
            "✏️ Modificar usuario",
            "📋 Ver todos los usuarios",
            "🔒 Cerrar sesión admin"
        )
        bot.send_message(message.chat.id, "Panel de administración", reply_markup=kb)
    except Exception:
        logger.exception("Error mostrando admin menu")

@bot.message_handler(func=lambda m: m.text == "🔒 Cerrar sesión admin")
def admin_logout(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
        return
    clear_admin_state(message.from_user.id)
    bot.send_message(message.chat.id, "Sesión de administración cerrada.", reply_markup=types.ReplyKeyboardRemove())

# -------------------------
# Verificar usuario
# -------------------------
@bot.message_handler(func=lambda m: m.text == "🔍 Verificar usuario")
def verify_user(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.send_message(message.chat.id, "Introduce el Telegram ID (número):")
    bot.register_next_step_handler(msg, process_verify)

def process_verify(message: telebot.types.Message):
    try:
        if not is_admin(message.from_user.id):
            return
        t_id = safe_int(message.text)
        if t_id is None:
            bot.send_message(message.chat.id, "ID no válido. Introduce solo números.")
            return
        user = get_user(t_id)
        if not user:
            bot.send_message(message.chat.id, "❌ Usuario no encontrado.")
            return
        text = (
            f"🆔 ID: {user['telegram_id']}\n"
            f"👤 Username: @{user.get('username','')}\n"
            f"📱 Teléfono: {user.get('telefono')}\n"
            f"📅 Registro: {user.get('fecha_registro')}\n"
            f"Nombre: {user.get('nombre')}\n"
            f"Apellido: {user.get('apellido')}\n"
            f"Plan: {user.get('plan')}\n"
            f"Grupo: {user.get('grupo')}\n"
            f"Academia: {user.get('academia')}"
        )
        bot.send_message(message.chat.id, text)
    except Exception:
        logger.exception("Error en process_verify")
        bot.send_message(message.chat.id, "Ha ocurrido un error al verificar el usuario.")

# -------------------------
# Registrar / Modificar usuario
# -------------------------
@bot.message_handler(func=lambda m: m.text in ["📝 Registrar usuario", "✏️ Modificar usuario"])
def edit_user(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.send_message(message.chat.id, "Telegram ID del usuario (solo números):")
    bot.register_next_step_handler(msg, edit_step_1)

def edit_step_1(message: telebot.types.Message):
    try:
        admin_id = message.from_user.id
        if not is_admin(admin_id):
            return
        telegram_id = safe_int(message.text)
        if telegram_id is None:
            bot.send_message(message.chat.id, "ID no válido.")
            return
        user = get_user(telegram_id)
        if not user:
            bot.send_message(message.chat.id, "❌ Usuario no encontrado.")
            return
        # Guardar estado
        set_admin_state(admin_id, {"target": telegram_id, "step": "nombre"})
        msg = bot.send_message(message.chat.id, "Ingrese Nombre:")
        bot.register_next_step_handler(msg, edit_step_2)
    except Exception:
        logger.exception("Error en edit_step_1")
        bot.send_message(message.chat.id, "Ha ocurrido un error al iniciar la edición.")

def edit_step_2(message: telebot.types.Message):
    try:
        admin_id = message.from_user.id
        state = get_admin_state(admin_id)
        if not state:
            bot.send_message(message.chat.id, "Estado no encontrado. Reinicia el proceso.")
            return
        target = state["target"]
        users.update_one({"telegram_id": target}, {"$set": {"nombre": message.text}})
        set_admin_state(admin_id, {"target": target, "step": "apellido"})
        msg = bot.send_message(message.chat.id, "Ingrese Apellido:")
        bot.register_next_step_handler(msg, edit_step_3)
    except Exception:
        logger.exception("Error en edit_step_2")
        bot.send_message(message.chat.id, "Ha ocurrido un error.")

def edit_step_3(message: telebot.types.Message):
    try:
        admin_id = message.from_user.id
        state = get_admin_state(admin_id)
        if not state:
            bot.send_message(message.chat.id, "Estado no encontrado. Reinicia el proceso.")
            return
        target = state["target"]
        users.update_one({"telegram_id": target}, {"$set": {"apellido": message.text}})
        set_admin_state(admin_id, {"target": target, "step": "plan"})
        msg = bot.send_message(message.chat.id, f"Ingrese Plan ({'/'.join(VALID_PLANS)}):")
        bot.register_next_step_handler(msg, edit_step_4)
    except Exception:
        logger.exception("Error en edit_step_3")
        bot.send_message(message.chat.id, "Ha ocurrido un error.")

def edit_step_4(message: telebot.types.Message):
    try:
        admin_id = message.from_user.id
        state = get_admin_state(admin_id)
        if not state:
            bot.send_message(message.chat.id, "Estado no encontrado. Reinicia el proceso.")
            return
        target = state["target"]
        plan = message.text.strip()
        if plan not in VALID_PLANS:
            bot.send_message(message.chat.id, f"Plan inválido. Debe ser uno de: {', '.join(VALID_PLANS)}")
            # Volvemos a pedir
            msg = bot.send_message(message.chat.id, f"Ingrese Plan ({'/'.join(VALID_PLANS)}):")
            bot.register_next_step_handler(msg, edit_step_4)
            return
        users.update_one({"telegram_id": target}, {"$set": {"plan": plan}})
        set_admin_state(admin_id, {"target": target, "step": "grupo"})
        msg = bot.send_message(message.chat.id, f"Ingrese Grupo ({'/'.join(VALID_GROUPS)}):")
        bot.register_next_step_handler(msg, edit_step_5)
    except Exception:
        logger.exception("Error en edit_step_4")
        bot.send_message(message.chat.id, "Ha ocurrido un error.")

def edit_step_5(message: telebot.types.Message):
    try:
        admin_id = message.from_user.id
        state = get_admin_state(admin_id)
        if not state:
            bot.send_message(message.chat.id, "Estado no encontrado. Reinicia el proceso.")
            return
        target = state["target"]
        grupo = message.text.strip()
        if grupo not in VALID_GROUPS:
            bot.send_message(message.chat.id, f"Grupo inválido. Debe ser uno de: {', '.join(VALID_GROUPS)}")
            msg = bot.send_message(message.chat.id, f"Ingrese Grupo ({'/'.join(VALID_GROUPS)}):")
            bot.register_next_step_handler(msg, edit_step_5)
            return
        users.update_one({"telegram_id": target}, {"$set": {"grupo": grupo}})
        set_admin_state(admin_id, {"target": target, "step": "academia"})
        msg = bot.send_message(message.chat.id, f"Ingrese Academia ({'/'.join(VALID_ACADEMIES)}):")
        bot.register_next_step_handler(msg, edit_step_6)
    except Exception:
        logger.exception("Error en edit_step_5")
        bot.send_message(message.chat.id, "Ha ocurrido un error.")

def edit_step_6(message: telebot.types.Message):
    try:
        admin_id = message.from_user.id
        state = get_admin_state(admin_id)
        if not state:
            bot.send_message(message.chat.id, "Estado no encontrado. Reinicia el proceso.")
            return
        target = state["target"]
        academia = message.text.strip()
        if academia not in VALID_ACADEMIES:
            bot.send_message(message.chat.id, f"Academia inválida. Debe ser uno de: {', '.join(VALID_ACADEMIES)}")
            msg = bot.send_message(message.chat.id, f"Ingrese Academia ({'/'.join(VALID_ACADEMIES)}):")
            bot.register_next_step_handler(msg, edit_step_6)
            return
        users.update_one({"telegram_id": target}, {"$set": {"academia": academia}})
        clear_admin_state(admin_id)
        bot.send_message(message.chat.id, "✅ Usuario actualizado correctamente.", reply_markup=types.ReplyKeyboardRemove())
    except Exception:
        logger.exception("Error en edit_step_6")
        bot.send_message(message.chat.id, "Ha ocurrido un error al finalizar la edición.")

# -------------------------
# Listar usuarios (con paginación inline)
# -------------------------
def build_users_page(page: int) -> (str, InlineKeyboardMarkup):
    total = users.count_documents({})
    skip = page * PAGE_SIZE
    cursor = users.find().skip(skip).limit(PAGE_SIZE)
    lines: List[str] = []
    for u in cursor:
        lines.append(
            f"🆔 {u.get('telegram_id')} | @{u.get('username','')}\n"
            f"{u.get('nombre') or ''} {u.get('apellido') or ''} | {u.get('plan') or ''} | {u.get('grupo') or ''} | {u.get('academia') or ''}\n"
            "──────────────"
        )
    text = "\n".join(lines) or "No hay usuarios registrados."
    kb = InlineKeyboardMarkup()
    # Prev button
    if page > 0:
        kb.add(InlineKeyboardButton("⬅️ Anterior", callback_data=f"users_page:{page-1}"))
    # Next button
    if (skip + PAGE_SIZE) < total:
        kb.add(InlineKeyboardButton("Siguiente ➡️", callback_data=f"users_page:{page+1}"))
    return text, kb

@bot.message_handler(func=lambda m: m.text == "📋 Ver todos los usuarios")
def list_users(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
        return
    text, kb = build_users_page(0)
    bot.send_message(message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("users_page:"))
def users_page_callback(call: telebot.types.CallbackQuery):
    try:
        if not is_admin(call.from_user.id):
            return
        _, page_str = call.data.split(":")
        page = int(page_str)
        text, kb = build_users_page(page)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)
    except Exception:
        logger.exception("Error en users_page_callback")
        bot.answer_callback_query(call.id, "Error al cambiar de página")

# -------------------------
# Catch-all para mensajes no permitidos por usuarios
# -------------------------
@bot.message_handler(func=lambda m: True)
def catch_all(message: telebot.types.Message):
    # Si es admin, dejar que use los botones. Si es usuario normal, no hacer nada.
    if is_admin(message.from_user.id):
        # Permitir que admin use los comandos/teclas
        return
    # No responder a usuarios que intenten interactuar más allá del Start
    # Mantener silencio para evitar exposiciones de datos
    return

# -------------------------
# Run
# -------------------------
def main():
    logger.info("Arrancando bot (production-ready)")
    try:
        if POLLING:
            # polling con none_stop y timeout para resilencia
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        else:
            # Si quieres webhook, implementa aquí la lógica (no incluida por defecto)
            logger.error("Webhook mode no implementado en este entregable. Usa POLLING=true.")
    except Exception:
        logger.exception("Bot detenido por excepción")

if __name__ == "__main__":
    main()
