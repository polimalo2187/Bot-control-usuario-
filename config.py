# Archivo: config.py

import os
from pymongo import MongoClient

# --- Variables de entorno ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Validaciones básicas
if not TELEGRAM_TOKEN:
    raise ValueError("La variable de entorno TELEGRAM_TOKEN no está definida.")
if not MONGO_URI:
    raise ValueError("La variable de entorno MONGO_URI no está definida.")
if not ADMIN_ID:
    raise ValueError("La variable de entorno ADMIN_ID no está definida.")

# --- Conexión a MongoDB ---
try:
    client = MongoClient(MONGO_URI)
    db = client['user_management']
    users_col = db['users']
    print("Conexión a MongoDB exitosa.")
except Exception as e:
    print(f"Error al conectar con MongoDB: {e}")
    raise
