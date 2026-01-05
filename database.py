from pymongo import MongoClient, errors
from config import MONGO_URI
import logging

logger = logging.getLogger(__name__)

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["telegram_admin_bot"]
users = db["users"]

# Indice único en telegram_id
try:
    users.create_index("telegram_id", unique=True)
except errors.PyMongoError as e:
    logger.exception("No se pudo crear el índice en users: %s", e)
