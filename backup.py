import os, shutil
from datetime import datetime
from servicios import DB_PATH, BACKUP_DIR

def hacer_backup():
    if not os.path.exists(DB_PATH):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(BACKUP_DIR, f"backup_{ts}.db")
    shutil.copy2(DB_PATH, destino)
    return destino

def limpiar_backups_viejos(max_backups=30):
    if not os.path.exists(BACKUP_DIR):
        return
    archivos = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_")],
        reverse=True
    )
    for viejo in archivos[max_backups:]:
        os.remove(os.path.join(BACKUP_DIR, viejo))
