import os
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Text
from pymongo import MongoClient
from dotenv import load_dotenv
from pydantic import BaseModel

# ======================================================
# CONFIGURACIÓN BÁSICA
# ======================================================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ======================================================
# CONEXIÓN A MONGODB
# ======================================================

client = MongoClient(MONGO_URI)
db = client["empresa_db"]
users_col = db["users"]

# ======================================================
# MODELO DE USUARIO
# ======================================================

class User(BaseModel):
    telegram_id: int
    username: str
    telefono: str = ""
    nombre: str = ""
    apellido: str = ""
    plan: str = ""
    grupo: str = ""
    academia: str = ""
    fecha_registro: str

# ======================================================
# TECLADO INICIAL PARA USUARIO
# ======================================================

start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📲 Compartir teléfono", request_contact=True)]
    ],
    resize_keyboard=True
)

# ======================================================
# MENÚ DE ADMINISTRADOR
# ======================================================

def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📝 Registrar Usuario", callback_data="registrar"),
        InlineKeyboardButton("✏️ Modificar Usuario", callback_data="modificar"),
        InlineKeyboardButton("📋 Ver Todos Usuarios", callback_data="ver_todos"),
        InlineKeyboardButton("✅ Verificar Usuario", callback_data="verificar")
    )
    return kb

# ======================================================
# HANDLERS PARA USUARIOS
# ======================================================

@dp.message(Text(equals="Start", ignore_case=True))
async def cmd_start(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username or ""
    # Verifica si ya está registrado
    if users_col.find_one({"telegram_id": telegram_id}):
        await message.answer("Ya estás registrado.")
    else:
        await message.answer(
            "Bienvenido. Por favor comparte tu teléfono.",
            reply_markup=start_kb
        )

@dp.message(content_types=types.ContentType.CONTACT)
async def contact_handler(message: types.Message):
    if message.contact and message.contact.user_id == message.from_user.id:
        user_data = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username or "",
            telefono=message.contact.phone_number,
            fecha_registro=datetime.utcnow().isoformat()
        )
        users_col.insert_one(user_data.dict())
        await message.answer("¡Registro completado! Gracias por compartir tu teléfono.")

# ======================================================
# HANDLERS PARA ADMIN
# ======================================================

@dp.message()
async def admin_access(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Menú de administración:", reply_markup=admin_menu())

@dp.callback_query()
async def admin_callback(call: types.CallbackQuery):
    action = call.data
    if call.from_user.id != ADMIN_ID:
        await call.answer("No tienes permisos para esto.", show_alert=True)
        return

    # ==================================================
    # REGISTRAR USUARIO
    # ==================================================
    if action == "registrar":
        await call.message.answer("Ingrese el Telegram ID del usuario a registrar:")
        dp.register_message_handler(handle_register_id, state="REGISTER_ID")
        await call.answer()

    # ==================================================
    # MODIFICAR USUARIO
    # ==================================================
    elif action == "modificar":
        await call.message.answer("Ingrese el Telegram ID del usuario a modificar:")
        dp.register_message_handler(handle_modify_id, state="MODIFY_ID")
        await call.answer()

    # ==================================================
    # VER TODOS USUARIOS
    # ==================================================
    elif action == "ver_todos":
        all_users = list(users_col.find({}))
        if not all_users:
            await call.message.answer("No hay usuarios registrados.")
        else:
            text = "Usuarios registrados:\n"
            for u in all_users:
                text += f"- {u.get('nombre', '')} {u.get('apellido', '')} | Plan: {u.get('plan', '')} | Grupo: {u.get('grupo', '')} | Academia: {u.get('academia', '')}\n"
            await call.message.answer(text)
        await call.answer()

    # ==================================================
    # VERIFICAR USUARIO
    # ==================================================
    elif action == "verificar":
        await call.message.answer("Ingrese el Telegram ID del usuario a verificar:")
        dp.register_message_handler(handle_verify_id, state="VERIFY_ID")
        await call.answer()

# ======================================================
# FUNCIONES AUXILIARES PARA ADMIN
# ======================================================

async def handle_register_id(message: types.Message):
    telegram_id = int(message.text)
    if users_col.find_one({"telegram_id": telegram_id}):
        await message.answer("El usuario ya existe.")
        return
    # Creamos registro vacío y pedimos datos
    new_user = {
        "telegram_id": telegram_id,
        "username": "",
        "telefono": "",
        "nombre": "",
        "apellido": "",
        "plan": "",
        "grupo": "",
        "academia": "",
        "fecha_registro": datetime.utcnow().isoformat()
    }
    users_col.insert_one(new_user)
    await message.answer("Usuario registrado. Ahora puedes modificar sus datos con la opción 'Modificar Usuario'.")

async def handle_modify_id(message: types.Message):
    telegram_id = int(message.text)
    user = users_col.find_one({"telegram_id": telegram_id})
    if not user:
        await message.answer("Usuario no encontrado.")
        return
    await message.answer(
        "Ingrese los datos en el siguiente formato:\n"
        "nombre,apellido,plan,grupo,academia\n"
        "Ejemplo: Juan,Perez,Premium,Grupo Premium,Academia Premium"
    )
    dp.register_message_handler(lambda m: handle_modify_data(m, telegram_id), state="MODIFY_DATA")

async def handle_modify_data(message: types.Message, telegram_id: int):
    try:
        nombre, apellido, plan, grupo, academia = [x.strip() for x in message.text.split(",")]
        users_col.update_one(
            {"telegram_id": telegram_id},
            {"$set": {
                "nombre": nombre,
                "apellido": apellido,
                "plan": plan,
                "grupo": grupo,
                "academia": academia
            }}
        )
        await message.answer("Datos actualizados correctamente.")
    except Exception:
        await message.answer("Formato incorrecto. Debes usar: nombre,apellido,plan,grupo,academia")

async def handle_verify_id(message: types.Message):
    telegram_id = int(message.text)
    user = users_col.find_one({"telegram_id": telegram_id})
    if not user:
        await message.answer("Usuario no encontrado.")
    else:
        await message.answer(
            f"Usuario verificado:\n"
            f"Nombre: {user.get('nombre', '')}\n"
            f"Apellido: {user.get('apellido', '')}\n"
            f"Plan: {user.get('plan', '')}\n"
            f"Grupo: {user.get('grupo', '')}\n"
            f"Academia: {user.get('academia', '')}\n"
            f"Teléfono: {user.get('telefono', '')}\n"
            f"Username: {user.get('username', '')}"
        )

# ======================================================
# ARRANQUE DEL BOT
# ======================================================

if __name__ == "__main__":
    import asyncio
    from aiogram import F

    async def main():
        logging.info("Bot iniciado")
        await dp.start_polling(bot)

    asyncio.run(main())
