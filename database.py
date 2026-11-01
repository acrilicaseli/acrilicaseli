import sqlite3
from servicios import DB_PATH, SERVICIOS, PRECIO_DECO_3D, PRECIO_DIJE


def conexion():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db():
    with conexion() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                telefono TEXT,
                fecha TEXT NOT NULL,
                horario TEXT NOT NULL,
                servicio TEXT NOT NULL,
                deco_3d INTEGER DEFAULT 0,
                dijes INTEGER DEFAULT 0,
                total INTEGER NOT NULL,
                senia INTEGER DEFAULT 0,
                pagado INTEGER DEFAULT 0,
                captura TEXT,
                token TEXT,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fecha, horario)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                clave TEXT PRIMARY KEY,
                valor TEXT
            )
        """)
        _migrar_columnas(conn)
        _seed_precios(conn)


def _migrar_columnas(conn):
    """Agrega columnas nuevas si la DB ya existía sin ellas."""
    columnas = [r["name"] for r in conn.execute("PRAGMA table_info(turnos)").fetchall()]
    for col, definicion in [
        ("senia", "INTEGER DEFAULT 0"),
        ("pagado", "INTEGER DEFAULT 0"),
        ("captura", "TEXT"),
        ("token", "TEXT"),
    ]:
        if col not in columnas:
            conn.execute(f"ALTER TABLE turnos ADD COLUMN {col} {definicion}")


def _seed_precios(conn):
    for nombre, precio in SERVICIOS.items():
        conn.execute(
            "INSERT OR IGNORE INTO config (clave, valor) VALUES (?, ?)",
            (f"precio::{nombre}", str(precio))
        )
    conn.execute("INSERT OR IGNORE INTO config (clave, valor) VALUES (?, ?)",
                 ("precio_deco_3d", str(PRECIO_DECO_3D)))
    conn.execute("INSERT OR IGNORE INTO config (clave, valor) VALUES (?, ?)",
                 ("precio_dije", str(PRECIO_DIJE)))


def guardar_config(clave, valor):
    with conexion() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO config (clave, valor) VALUES (?, ?)",
            (clave, str(valor))
        )


def leer_config(clave, default=None):
    with conexion() as conn:
        row = conn.execute(
            "SELECT valor FROM config WHERE clave = ?", (clave,)
        ).fetchone()
        return row["valor"] if row else default


def obtener_precios():
    with conexion() as conn:
        rows = conn.execute(
            "SELECT clave, valor FROM config WHERE clave LIKE 'precio::%'"
        ).fetchall()
    servicios = {r["clave"].replace("precio::", ""): int(r["valor"]) for r in rows}
    deco = int(leer_config("precio_deco_3d", PRECIO_DECO_3D))
    dije = int(leer_config("precio_dije", PRECIO_DIJE))
    return servicios, deco, dije


def insertar_turno(turno):
    with conexion() as conn:
        cur = conn.execute("""
            INSERT INTO turnos (cliente, telefono, fecha, horario, servicio,
                                deco_3d, dijes, total, senia, pagado, captura, token)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            turno["cliente"], turno.get("telefono", ""), turno["fecha"],
            turno["horario"], turno["servicio"], turno["deco_3d"],
            turno["dijes"], turno["total"],
            turno.get("senia", 0), turno.get("pagado", 0),
            turno.get("captura"), turno.get("token")
        ))
        return cur.lastrowid


def obtener_turnos(fecha=None):
    with conexion() as conn:
        if fecha:
            rows = conn.execute(
                "SELECT * FROM turnos WHERE fecha = ? ORDER BY horario",
                (fecha,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM turnos ORDER BY fecha DESC, horario"
            ).fetchall()
        return [dict(r) for r in rows]


def obtener_turno_por_token(token):
    with conexion() as conn:
        row = conn.execute(
            "SELECT * FROM turnos WHERE token = ?", (token,)
        ).fetchone()
        return dict(row) if row else None


def eliminar_turno(turno_id):
    with conexion() as conn:
        conn.execute("DELETE FROM turnos WHERE id = ?", (turno_id,))


def horario_ocupado(fecha, horario):
    with conexion() as conn:
        row = conn.execute(
            "SELECT 1 FROM turnos WHERE fecha = ? AND horario = ?",
            (fecha, horario)
        ).fetchone()
        return row is not None


def horarios_ocupados(fecha):
    with conexion() as conn:
        rows = conn.execute(
            "SELECT horario FROM turnos WHERE fecha = ?", (fecha,)
        ).fetchall()
        return [r["horario"] for r in rows]


def marcar_pagado(turno_id, pagado=1):
    with conexion() as conn:
        conn.execute("UPDATE turnos SET pagado = ? WHERE id = ?", (pagado, turno_id))