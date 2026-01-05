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
admin_states: Dict[int, Dict[str, Any]] = {}

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
# Constantes
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
# START — registro automático del usuario
# -------------------------
@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    try:
        telegram_id = message.from_user.id
        username = message.from_user.username or ""

        if get_user(telegram_id):
            bot.send_message(message.chat.id, "✅ Ya estás registrado.")
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

        bot.send_message(message.chat.id, "✅ Registro completado correctamente.")
        logger.info("Usuario registrado: %s (@%s)", telegram_id, username)

    except Exception:
        logger.exception("Error en /start")
        bot.send_message(message.chat.id, "Ha ocurrido un error. Inténtalo más tarde.")

# -------------------------
# MENÚ ADMIN
# -------------------------
@bot.message_handler(commands=["admin"])
def admin_menu(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
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

@bot.message_handler(func=lambda m: m.text == "🔒 Cerrar sesión admin")
def admin_logout(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
        return
    clear_admin_state(message.from_user.id)
    bot.send_message(message.chat.id, "Sesión de administración cerrada.", reply_markup=types.ReplyKeyboardRemove())

# -------------------------
# VERIFICAR USUARIO
# -------------------------
@bot.message_handler(func=lambda m: m.text == "🔍 Verificar usuario")
def verify_user(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.send_message(message.chat.id, "Introduce el Telegram ID:")
    bot.register_next_step_handler(msg, process_verify)

def process_verify(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
        return

    t_id = safe_int(message.text)
    if t_id is None:
        bot.send_message(message.chat.id, "ID no válido.")
        return

    user = get_user(t_id)
    if not user:
        bot.send_message(message.chat.id, "❌ Usuario no encontrado.")
        return

    bot.send_message(
        message.chat.id,
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

# -------------------------
# REGISTRAR / MODIFICAR USUARIO
# -------------------------
@bot.message_handler(func=lambda m: m.text in ["📝 Registrar usuario", "✏️ Modificar usuario"])
def edit_user(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.send_message(message.chat.id, "Telegram ID del usuario:")
    bot.register_next_step_handler(msg, edit_step_1)

def edit_step_1(message):
    telegram_id = safe_int(message.text)
    if telegram_id is None or not get_user(telegram_id):
        bot.send_message(message.chat.id, "Usuario no encontrado.")
        return
    set_admin_state(message.from_user.id, {"target": telegram_id})
    msg = bot.send_message(message.chat.id, "Ingrese Nombre:")
    bot.register_next_step_handler(msg, edit_step_2)

def edit_step_2(message):
    state = get_admin_state(message.from_user.id)
    users.update_one({"telegram_id": state["target"]}, {"$set": {"nombre": message.text}})
    msg = bot.send_message(message.chat.id, "Ingrese Apellido:")
    bot.register_next_step_handler(msg, edit_step_3)

def edit_step_3(message):
    state = get_admin_state(message.from_user.id)
    users.update_one({"telegram_id": state["target"]}, {"$set": {"apellido": message.text}})
    msg = bot.send_message(message.chat.id, f"Ingrese Plan ({'/'.join(VALID_PLANS)}):")
    bot.register_next_step_handler(msg, edit_step_4)

def edit_step_4(message):
    if message.text not in VALID_PLANS:
        bot.send_message(message.chat.id, "Plan inválido.")
        return
    state = get_admin_state(message.from_user.id)
    users.update_one({"telegram_id": state["target"]}, {"$set": {"plan": message.text}})
    msg = bot.send_message(message.chat.id, f"Ingrese Grupo ({'/'.join(VALID_GROUPS)}):")
    bot.register_next_step_handler(msg, edit_step_5)

def edit_step_5(message):
    if message.text not in VALID_GROUPS:
        bot.send_message(message.chat.id, "Grupo inválido.")
        return
    state = get_admin_state(message.from_user.id)
    users.update_one({"telegram_id": state["target"]}, {"$set": {"grupo": message.text}})
    msg = bot.send_message(message.chat.id, f"Ingrese Academia ({'/'.join(VALID_ACADEMIES)}):")
    bot.register_next_step_handler(msg, edit_step_6)

def edit_step_6(message):
    if message.text not in VALID_ACADEMIES:
        bot.send_message(message.chat.id, "Academia inválida.")
        return
    state = get_admin_state(message.from_user.id)
    users.update_one({"telegram_id": state["target"]}, {"$set": {"academia": message.text}})
    msg = bot.send_message(message.chat.id, "Ingrese Teléfono:")
    bot.register_next_step_handler(msg, edit_step_7)

def edit_step_7(message):
    state = get_admin_state(message.from_user.id)
    users.update_one({"telegram_id": state["target"]}, {"$set": {"telefono": message.text}})
    clear_admin_state(message.from_user.id)
    bot.send_message(message.chat.id, "✅ Usuario actualizado correctamente.", reply_markup=types.ReplyKeyboardRemove())

# -------------------------
# LISTAR USUARIOS
# -------------------------
def build_users_page(page: int):
    skip = page * PAGE_SIZE
    cursor = users.find().skip(skip).limit(PAGE_SIZE)
    text = "\n".join(
        f"{u['telegram_id']} | @{u.get('username','')} | {u.get('plan')}"
        for u in cursor
    ) or "No hay usuarios."
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️", callback_data=f"users_page:{page-1}"))
    kb.add(InlineKeyboardButton("➡️", callback_data=f"users_page:{page+1}"))
    return text, kb

@bot.message_handler(func=lambda m: m.text == "📋 Ver todos los usuarios")
def list_users(message):
    text, kb = build_users_page(0)
    bot.send_message(message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("users_page:"))
def page_callback(call):
    page = int(call.data.split(":")[1])
    text, kb = build_users_page(page)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

# -------------------------
# RUN
# -------------------------
def main():
    logger.info("Bot iniciado en PRODUCCIÓN")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    main()
