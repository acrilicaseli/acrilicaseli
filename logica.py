import secrets
from datetime import datetime
from database import (
    insertar_turno, obtener_turnos, eliminar_turno,
    horario_ocupado as db_horario_ocupado, obtener_precios
)


def calcular_total(servicio, deco, dijes, precios=None, precio_deco=None, precio_dije=None):
    if precios is None:
        precios, precio_deco, precio_dije = obtener_precios()
    base = precios.get(servicio, 0)
    return base + deco * precio_deco + dijes * precio_dije


def calcular_senia(total, porcentaje=0.30):
    return round(total * porcentaje)


def crear_turno(cliente, telefono, fecha, horario, servicio, deco, dijes, captura=None):
    if db_horario_ocupado(fecha, horario):
        raise ValueError("Ese horario ya está ocupado.")
    total = calcular_total(servicio, deco, dijes)
    turno = {
        "cliente": cliente,
        "telefono": telefono,
        "fecha": fecha,
        "horario": horario,
        "servicio": servicio,
        "deco_3d": deco,
        "dijes": dijes,
        "total": total,
        "senia": calcular_senia(total),
        "pagado": 0,
        "captura": captura,
        "token": secrets.token_urlsafe(16),   # token único para el link del PDF
    }
    turno["id"] = insertar_turno(turno)
    return turno


def listar_turnos(fecha=None):
    return obtener_turnos(fecha)


def cancelar_turno(turno_id):
    eliminar_turno(turno_id)


def calcular_ganancias(fecha=None):
    turnos = obtener_turnos(fecha)
    return sum(t["total"] for t in turnos), len(turnos)


def ganancias_por_mes():
    turnos = obtener_turnos()
    por_mes = {}
    for t in turnos:
        try:
            fecha = datetime.strptime(t["fecha"], "%Y-%m-%d")
        except ValueError:
            try:
                fecha = datetime.strptime(t["fecha"], "%d/%m/%Y")
            except ValueError:
                continue
        clave = fecha.strftime("%m/%Y")
        por_mes[clave] = por_mes.get(clave, 0) + t["total"]
    return dict(sorted(por_mes.items()))