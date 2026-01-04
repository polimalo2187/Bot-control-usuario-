# Archivo: callbacks.py

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import Dispatcher
from db_utils import modify_user_field

# --- Botones Inline ---
def plan_buttons():
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("Free", callback_data="plan_Free"),
        InlineKeyboardButton("Plus", callback_data="plan_Plus"),
        InlineKeyboardButton("Premium", callback_data="plan_Premium")
    )
    return kb

def group_buttons():
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("Grupo Free", callback_data="group_Free"),
        InlineKeyboardButton("Grupo Plus", callback_data="group_Plus"),
        InlineKeyboardButton("Grupo Premium", callback_data="group_Premium")
    )
    return kb

def academy_buttons():
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("Academia Free", callback_data="academy_Free"),
        InlineKeyboardButton("Academia Plus", callback_data="academy_Plus"),
        InlineKeyboardButton("Academia Premium", callback_data="academy_Premium")
    )
    return kb

# --- Callback Handler ---
async def callback_handler(call: CallbackQuery):
    """
    Maneja la selección de Plan, Grupo y Academia.
    Se espera que call.data tenga el formato 'plan_X', 'group_X' o 'academy_X'
    """
    data = call.data
    chat_id = call.message.chat.id

    # El chat_id será usado como telegram_id para simplificar el ejemplo
    telegram_id = chat_id

    if data.startswith("plan_"):
        plan = data.split("_")[1]
        modify_user_field(telegram_id, "plan", plan)
        await call.message.edit_text(f"Plan actualizado a: {plan}")
        # Luego pedimos seleccionar Grupo
        await call.message.answer("Selecciona el Grupo del usuario:", reply_markup=group_buttons())

    elif data.startswith("group_"):
        group = data.split("_")[1]
        modify_user_field(telegram_id, "group", group)
        await call.message.edit_text(f"Grupo actualizado a: {group}")
        # Luego pedimos seleccionar Academia
        await call.message.answer("Selecciona la Academia del usuario:", reply_markup=academy_buttons())

    elif data.startswith("academy_"):
        academy = data.split("_")[1]
        modify_user_field(telegram_id, "academy", academy)
        await call.message.edit_text(f"Academia actualizada a: {academy}\nRegistro completo ✅")

# --- Función para registrar callbacks en Dispatcher ---
def register_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(callback_handler, lambda call: True)
