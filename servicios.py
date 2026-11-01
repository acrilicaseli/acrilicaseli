import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

NOMBRE_NEGOCIO = "Uñas Acrílicas Elii Rodríguez"
DB_PATH = "eli_acrilicas.db"
TICKETS_DIR = "tickets"
BACKUP_DIR = "backups"
CAPTURAS_DIR = "capturas"

# === DATOS DE TRANSFERENCIA ===
ALIAS = "Acrilicaseli"
CBU = "0000003100007466959253"
TITULAR = "Eliana Yanina Rodriguez"
BANCO = "Mercado Pago"

# === SEÑA ===
PORCENTAJE_SENIA = 0.30

# === SERVICIOS Y PRECIOS ===
SERVICIOS = {
    "Largo #1": 21000,
    "Largo #2": 23000,
    "Largo #3": 25000,
    "Largo #4": 28000,
    "Largo #5": 30000,
    "Retiro": 8000,
    "Retiro de colega": 10000,
    "Semi en manos": 15000,
    "Semi en pies": 20000,
    "Acripie": 25000,
}

PRECIO_DECO_3D = 2000
PRECIO_DIJE = 1000

HORARIOS = ["08:00", "09:30", "14:00", "18:30"]

# === TWILIO SMS ===
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM = os.environ.get("TWILIO_FROM", "")
SMS_HERMANA = os.environ.get("SMS_HERMANA", "5491150141876")
URL_PUBLICA = os.environ.get("URL_PUBLICA", "http://localhost:5000")

# === Crear carpetas necesarias ===
for d in (TICKETS_DIR, BACKUP_DIR, CAPTURAS_DIR):
    os.makedirs(d, exist_ok=True)
if __name__ == "__main__":
    print("SID:", TWILIO_ACCOUNT_SID)
    print("TOKEN:", TWILIO_AUTH_TOKEN[:6] + "..." if TWILIO_AUTH_TOKEN else "vacío")
    print("FROM:", TWILIO_FROM)
    print("SMS_HERMANA:", SMS_HERMANA)
    print("URL_PUBLICA:", URL_PUBLICA)
 