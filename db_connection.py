"""
Conexión segura a MongoDB Atlas para el bot de Telegram
Escapa la contraseña para evitar errores de caracteres en la URI
"""

from urllib.parse import quote_plus
from pymongo import MongoClient

# -----------------------------
# Usuario y contraseña
# -----------------------------
usuario = "Carlos2187"
password = "21872187Crp"  # tu contraseña real

# Escapar contraseña para caracteres especiales
password_safe = quote_plus(password)

# Cluster y opciones
cluster = "controlusuario.oszzrpp.mongodb.net"
options = "appName=Controlusuario"

# URI final segura
MONGO_URI = f"mongodb+srv://{usuario}:{password_safe}@{cluster}/?{options}"

# -----------------------------
# Conexión al cliente MongoDB
# -----------------------------
client = MongoClient(MONGO_URI)

# Base de datos y colección de usuarios
db = client["telegram_bot"]
users = db["users"]

print("✅ Conexión segura a MongoDB Atlas exitosa.")
