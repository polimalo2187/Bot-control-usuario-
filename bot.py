import telebot
from telebot import types
from datetime import datetime

from config import BOT_TOKEN, ADMIN_IDS
from database import users

bot = telebot.TeleBot(BOT_TOKEN)


# ─────────────────────────────
# UTILIDADES
# ─────────────────────────────

def is_admin(user_id):
    return user_id in ADMIN_IDS


def get_user(telegram_id):
    return users.find_one({"telegram_id": telegram_id})


# ─────────────────────────────
# START USUARIO
# ─────────────────────────────

@bot.message_handler(commands=["start"])
def start(message):
    telegram_id = message.from_user.id
    username = message.from_user.username

    if get_user(telegram_id):
        bot.send_message(message.chat.id, "✅ Ya estás registrado.")
        return

    users.insert_one({
        "telegram_id": telegram_id,
        "username": username,
        "telefono": None,
        "fecha_registro": datetime.now(),
        "nombre": None,
        "apellido": None,
        "plan": None,
        "grupo": None,
        "academia": None
    })

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📱 Compartir teléfono", request_contact=True))

    bot.send_message(
        message.chat.id,
        "Por favor comparte tu número de teléfono para completar el registro.",
        reply_markup=kb
    )


@bot.message_handler(content_types=["contact"])
def save_phone(message):
    telegram_id = message.from_user.id

    users.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"telefono": message.contact.phone_number}}
    )

    bot.send_message(
        message.chat.id,
        "✅ Registro completado correctamente.",
        reply_markup=types.ReplyKeyboardRemove()
    )


# ─────────────────────────────
# MENÚ ADMIN
# ─────────────────────────────

@bot.message_handler(commands=["admin"])
def admin_menu(message):
    if not is_admin(message.from_user.id):
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        "🔍 Verificar usuario",
        "📝 Registrar usuario",
        "✏️ Modificar usuario",
        "📋 Ver todos los usuarios"
    )

    bot.send_message(message.chat.id, "Panel de administración", reply_markup=kb)


# ─────────────────────────────
# VERIFICAR USUARIO
# ─────────────────────────────

@bot.message_handler(func=lambda m: m.text == "🔍 Verificar usuario")
def verify_user(message):
    msg = bot.send_message(message.chat.id, "Introduce el Telegram ID:")
    bot.register_next_step_handler(msg, process_verify)


def process_verify(message):
    user = get_user(int(message.text))
    if not user:
        bot.send_message(message.chat.id, "❌ Usuario no encontrado.")
        return

    text = (
        f"🆔 ID: {user['telegram_id']}\n"
        f"👤 Username: @{user['username']}\n"
        f"📱 Teléfono: {user['telefono']}\n"
        f"📅 Registro: {user['fecha_registro']}"
    )

    bot.send_message(message.chat.id, text)


# ─────────────────────────────
# REGISTRAR / MODIFICAR USUARIO
# ─────────────────────────────

def ask_field(message, field, next_handler):
    msg = bot.send_message(message.chat.id, f"Ingrese {field}:")
    bot.register_next_step_handler(msg, next_handler)


@bot.message_handler(func=lambda m: m.text in ["📝 Registrar usuario", "✏️ Modificar usuario"])
def edit_user(message):
    msg = bot.send_message(message.chat.id, "Telegram ID del usuario:")
    bot.register_next_step_handler(msg, edit_step_1)


def edit_step_1(message):
    telegram_id = int(message.text)
    if not get_user(telegram_id):
        bot.send_message(message.chat.id, "❌ Usuario no encontrado.")
        return

    message.telegram_id_target = telegram_id
    ask_field(message, "Nombre", edit_step_2)


def edit_step_2(message):
    users.update_one(
        {"telegram_id": message.telegram_id_target},
        {"$set": {"nombre": message.text}}
    )
    ask_field(message, "Apellido", edit_step_3)


def edit_step_3(message):
    users.update_one(
        {"telegram_id": message.telegram_id_target},
        {"$set": {"apellido": message.text}}
    )
    ask_field(message, "Plan (Free / Plus / Premium)", edit_step_4)


def edit_step_4(message):
    users.update_one(
        {"telegram_id": message.telegram_id_target},
        {"$set": {"plan": message.text}}
    )
    ask_field(message, "Grupo", edit_step_5)


def edit_step_5(message):
    users.update_one(
        {"telegram_id": message.telegram_id_target},
        {"$set": {"grupo": message.text}}
    )
    ask_field(message, "Academia", edit_step_6)


def edit_step_6(message):
    users.update_one(
        {"telegram_id": message.telegram_id_target},
        {"$set": {"academia": message.text}}
    )

    bot.send_message(message.chat.id, "✅ Usuario actualizado correctamente.")


# ─────────────────────────────
# LISTAR USUARIOS
# ─────────────────────────────

@bot.message_handler(func=lambda m: m.text == "📋 Ver todos los usuarios")
def list_users(message):
    text = ""
    for u in users.find():
        text += (
            f"\n🆔 {u['telegram_id']} | @{u['username']}\n"
            f"{u['nombre']} {u['apellido']} | {u['plan']} | {u['grupo']} | {u['academia']}\n"
            "──────────────"
        )

    bot.send_message(message.chat.id, text or "No hay usuarios registrados.")


# ─────────────────────────────
# RUN
# ─────────────────────────────

bot.infinity_polling()
