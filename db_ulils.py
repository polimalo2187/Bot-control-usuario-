# Archivo: db_utils.py

from datetime import datetime
from config import users_col

# --- Función para registrar un usuario ---
def register_user(telegram_id, username, phone=None, first_name="", last_name="", plan="", group="", academy=""):
    """
    Registra un nuevo usuario en la base de datos o actualiza si ya existe.
    """
    user = users_col.find_one({"telegram_id": telegram_id})
    if user:
        # Si ya existe, actualiza algunos campos opcionales
        update_fields = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "plan": plan,
            "group": group,
            "academy": academy
        }
        if phone:
            update_fields["phone"] = phone
        users_col.update_one({"telegram_id": telegram_id}, {"$set": update_fields})
        return "Usuario actualizado correctamente."
    else:
        # Insertar nuevo usuario
        user_doc = {
            "telegram_id": telegram_id,
            "username": username,
            "phone": phone,
            "first_name": first_name,
            "last_name": last_name,
            "plan": plan,
            "group": group,
            "academy": academy,
            "registration_date": datetime.utcnow()
        }
        users_col.insert_one(user_doc)
        return "Usuario registrado correctamente."

# --- Función para modificar un campo específico ---
def modify_user_field(telegram_id, field_name, new_value):
    """
    Modifica un campo específico de un usuario.
    """
    valid_fields = ["first_name", "last_name", "plan", "group", "academy", "phone", "username"]
    if field_name not in valid_fields:
        return f"Campo '{field_name}' no válido."
    
    result = users_col.update_one({"telegram_id": telegram_id}, {"$set": {field_name: new_value}})
    if result.matched_count:
        return f"{field_name} actualizado correctamente."
    else:
        return "Usuario no encontrado."

# --- Función para verificar usuario por Telegram ID ---
def verify_user(telegram_id):
    """
    Devuelve los datos de un usuario según su Telegram ID.
    """
    user = users_col.find_one({"telegram_id": telegram_id})
    if user:
        return {
            "telegram_id": user.get("telegram_id"),
            "username": user.get("username", ""),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "plan": user.get("plan", ""),
            "group": user.get("group", ""),
            "academy": user.get("academy", ""),
            "phone": user.get("phone", ""),
            "registration_date": user.get("registration_date")
        }
    else:
        return None

# --- Función para listar todos los usuarios ---
def list_all_users():
    """
    Devuelve una lista de todos los usuarios en la base de datos.
    """
    users = users_col.find()
    user_list = []
    for user in users:
        user_list.append({
            "telegram_id": user.get("telegram_id"),
            "username": user.get("username", ""),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "plan": user.get("plan", ""),
            "group": user.get("group", ""),
            "academy": user.get("academy", ""),
            "phone": user.get("phone", ""),
            "registration_date": user.get("registration_date")
        })
    return user_list
