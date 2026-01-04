import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno (opcional si usas .env local)
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Inicializar bot y dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Conectar a MongoDB
client = MongoClient(MONGO_URI)
db = client["bot_database"]
users_collection = db["users"]

# ---------------------
# Funciones de ejemplo
# ---------------------

@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    phone_button = types.KeyboardButton(
        text="Compartir mi número de teléfono", request_contact=True
    )
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(phone_button)
    
    # Guardar usuario si no existe
    if users_collection.find_one({"telegram_id": user_id}) is None:
        users_collection.insert_one({
            "telegram_id": user_id,
            "username": username,
            "phone": None,
            "registered_at": message.date
        })
    
    await message.answer(
        "Bienvenido al bot de gestión. Por favor comparte tu teléfono.",
        reply_markup=keyboard
    )

@dp.message(content_types=types.ContentType.CONTACT)
async def contact_handler(message: types.Message):
    contact = message.contact
    users_collection.update_one(
        {"telegram_id": contact.user_id},
        {"$set": {"phone": contact.phone_number}}
    )
    await message.answer("¡Teléfono registrado correctamente! ✅")

# ---------------------
# Iniciar bot
# ---------------------
if __name__ == "__main__":
    logging.info("Bot iniciado...")
    asyncio.run(dp.start_polling(bot))
