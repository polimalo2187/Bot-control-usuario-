# Archivo: admin_handlers.py

from aiogram import types
from aiogram.dispatcher import Dispatcher
from db_utils import verify_user, list_all_users, register_user, modify_user_field
from callbacks import plan_buttons
from aiogram.types import ReplyKeyboardRemove

# --- Verificar usuario ---
async def verify_user_handler(message: types.Message):
    try:
        telegram_id = int(message.text)
        user_data = verify_user(telegram_id)
        if user_data:
            msg = f"✅ Usuario encontrado:\n" \
                  f"ID: {user_data['telegram_id']}\n" \
                  f"Username: {user_data['username']}\n" \
                  f"Nombre: {user_data['first_name']} {user_data['last_name']}\n" \
                  f"Plan: {user_data['plan']}\n" \
                  f"Grupo: {user_data['group']}\n" \
                  f"Academia: {user_data['academy']}"
            await message.answer(msg)
        else:
            await message.answer("❌ Usuario no encontrado.")
    except ValueError:
        await message.answer("ID inválido. Debe ser un número.")

# --- Registrar usuario ---
async def register_user_handler(message: types.Message, dp: Dispatcher):
    try:
        telegram_id = int(message.text)
        user_data = verify_user(telegram_id)
        if not user_data:
            await message.answer("Este usuario aún no tiene contacto. Pídeles que hagan /start primero.")
            return

        await message.answer("Ingresa el nombre y apellido del usuario (Nombre Apellido):")

        # Espera el siguiente mensaje con nombre completo
        def name_filter(msg: types.Message):
            return msg.from_user.id == message.from_user.id

        async def set_name(msg: types.Message):
            parts = msg.text.strip().split()
            first_name = parts[0]
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
            register_user(telegram_id, user_data['username'], first_name=first_name, last_name=last_name)
            await msg.answer("Nombre registrado. Ahora selecciona el Plan:", reply_markup=plan_buttons())
            dp.unregister_message_handler(set_name, name_filter)

        dp.register_message_handler(set_name, name_filter)

    except ValueError:
        await message.answer("ID inválido. Debe ser un número.")

# --- Modificar usuario ---
async def modify_user_handler(message: types.Message, dp: Dispatcher):
    try:
        telegram_id = int(message.text)
        user_data = verify_user(telegram_id)
        if not user_data:
            await message.answer("Usuario no encontrado.")
            return

        # Menú de campos a modificar
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Nombre", "Apellido")
        keyboard.add("Plan", "Grupo", "Academia")
        keyboard.add("Cancelar")

        await message.answer("Selecciona el campo que deseas modificar:", reply_markup=keyboard)

        def field_filter(msg: types.Message):
            return msg.from_user.id == message.from_user.id

        async def modify_field(msg: types.Message):
            field = msg.text
            if field == "Cancelar":
                await msg.answer("Operación cancelada.", reply_markup=ReplyKeyboardRemove())
                dp.unregister_message_handler(modify_field, field_filter)
                return

            if field in ["Nombre", "Apellido"]:
                await msg.answer(f"Ingresa el nuevo {field}:")
                async def set_name_change(new_msg: types.Message):
                    value = new_msg.text.strip()
                    key = "first_name" if field == "Nombre" else "last_name"
                    modify_user_field(telegram_id, key, value)
                    await new_msg.answer(f"{field} actualizado correctamente.", reply_markup=ReplyKeyboardRemove())
                    dp.unregister_message_handler(set_name_change, field_filter)
                dp.register_message_handler(set_name_change, field_filter)

            elif field in ["Plan", "Grupo", "Academia"]:
                from callbacks import plan_buttons, group_buttons, academy_buttons
                if field == "Plan":
                    kb = plan_buttons()
                elif field == "Grupo":
                    kb = group_buttons()
                else:
                    kb = academy_buttons()
                await msg.answer(f"Selecciona el nuevo {field}:", reply_markup=kb)

            dp.unregister_message_handler(modify_field, field_filter)

        dp.register_message_handler(modify_field, field_filter)

    except ValueError:
        await message.answer("ID inválido. Debe ser un número.")

# --- Listar todos los usuarios ---
async def list_users_handler(message: types.Message):
    users = list_all_users()
    if not users:
        await message.answer("No hay usuarios registrados.")
        return

    msg = ""
    for u in users:
        msg += f"ID: {u['telegram_id']}\nUsername: {u['username']}\n" \
               f"Nombre: {u['first_name']} {u['last_name']}\n" \
               f"Plan: {u['plan']}\nGrupo: {u['group']}\nAcademia: {u['academy']}\n\n"
    await message.answer(msg)

# --- Función para registrar handlers del admin ---
def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(verify_user_handler, lambda msg: msg.text == "✅ Verificar usuario")
    dp.register_message_handler(list_users_handler, lambda msg: msg.text == "📋 Ver todos los usuarios")
    dp.register_message_handler(lambda msg: register_user_handler(msg, dp), lambda msg: msg.text == "📝 Registrar usuario")
    dp.register_message_handler(lambda msg: modify_user_handler(msg, dp), lambda msg: msg.text == "✏️ Modificar usuario")
