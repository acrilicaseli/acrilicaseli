import hashlib
from database import guardar_config, leer_config

SALT = "eli_salt_2025"

def hash_password(password):
    return hashlib.sha256((password + SALT).encode()).hexdigest()

def configurar_password_inicial(password):
    guardar_config("password_hash", hash_password(password))

def verificar_password(password):
    hash_guardado = leer_config("password_hash")
    if not hash_guardado:
        configurar_password_inicial(password)
        return True
    return hash_password(password) == hash_guardado
