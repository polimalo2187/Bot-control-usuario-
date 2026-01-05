import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
POLLING = os.getenv("POLLING", "true").lower() in ("1", "true", "yes")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN no está configurado en .env")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI no está configurado en .env")

def parse_admin_ids(raw: str):
    ids = []
    for part in raw.split(","):
        p = part.strip()
        if not p:
            continue
        try:
            ids.append(int(p))
        except ValueError:
            raise RuntimeError(f"ADMIN_IDS contiene un valor no válido: {p}")
    return ids

ADMIN_IDS = parse_admin_ids(ADMIN_IDS_RAW)
