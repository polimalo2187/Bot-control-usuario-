# Archivo: BotP.py

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils import executor

# --- Importar módulos del proyecto ---
from config import TELEGRAM_TOKEN, ADMIN_ID
from db_utils import register_user, verify_user
from callbacks import register_callbacks
from admin_handlers import register_admin_handlers

# Configuración de logging
logging.basicConfig(level=logging.INFO)

# Inicializar bot y dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# --- Teclado principal para administrador ---
admin_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
admin_kb.add("✅ Verificar usuario", "📝 Registrar usuario")
admin_kb.add("✏️ Modificar usuario", "📋 Ver todos los usuarios")

# --- Comando /start ---
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    if telegram_id == ADMIN_ID:
        await message.answer("Bienvenido, Administrador. Menú principal:", reply_markup=admin_kb)
    else:
        # Registrar usuario normal
        result = register_user(telegram_id, username)
        await message.answer(
            "Bienvenido! Por favor comparte tu teléfono para completar el registro.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                types.KeyboardButton("📲 Compartir teléfono", request_contact=True)
            )
        )

# --- Manejo del contacto del usuario ---
@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(message: types.Message):
    if message.contact.user_id != message.from_user.id:
        await message.answer("Por favor comparte tu propio número de teléfono.")
        return
    from db_utils import modify_user_field
    phone = message.contact.phone_number
    telegram_id = message.from_user.id
    modify_user_field(telegram_id, "phone", phone)
    await message.answer("Registro completado. Gracias!", reply_markup=ReplyKeyboardRemove())

# --- Registro de handlers del administrador ---
register_admin_handlers(dp)

# --- Registro de handlers de callbacks (Plan, Grupo, Academia) ---
register_callbacks(dp)

# --- Comando /help ---
@dp.message_handler(commands=["help"])
async def help_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Comandos de Administrador:\n✅ Verificar usuario\n📝 Registrar usuario\n✏️ Modificar usuario\n📋 Ver todos los usuarios")
    else:
        await message.answer("Este bot registra tu teléfono y datos para la gestión de usuarios. Presiona Start para comenzar.")

# --- Ejecutar bot ---
if __name__ == "__main__":
    logging.info("Bot iniciado...")
    executor.start_polling(dp, skip_updates=True)
