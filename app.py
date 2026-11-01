from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_from_directory
)
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import uuid
from dotenv import load_dotenv
load_dotenv()

from database import (
    inicializar_db, obtener_precios, guardar_config,
    horarios_ocupados, leer_config, marcar_pagado,
    obtener_turno_por_token
)
from logica import (
    crear_turno, listar_turnos, cancelar_turno,
    calcular_ganancias, ganancias_por_mes, calcular_senia
)
from servicios import (
    NOMBRE_NEGOCIO, HORARIOS, CAPTURAS_DIR, TICKETS_DIR,
    ALIAS, CBU, TITULAR, BANCO, PORCENTAJE_SENIA
)
from auth import verificar_password
from pdf_utils import generar_ticket_pdf

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambiar_esto_en_produccion")

EXTENSIONES_OK = {"png", "jpg", "jpeg", "webp", "gif"}


def extension_valida(nombre):
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in EXTENSIONES_OK


def guardar_captura(archivo):
    if not archivo or archivo.filename == "":
        return None
    if not extension_valida(archivo.filename):
        raise ValueError("Formato de imagen no válido (usá JPG, PNG o WEBP).")
    ext = archivo.filename.rsplit(".", 1)[1].lower()
    nombre = f"{uuid.uuid4().hex}.{ext}"
    ruta = os.path.join(CAPTURAS_DIR, nombre)
    archivo.save(ruta)
    return nombre


inicializar_db()


@app.route("/")
def index():
    precios, deco, dije = obtener_precios()
    return render_template("index.html",
                           nombre=NOMBRE_NEGOCIO,
                           servicios=precios,
                           precio_deco=deco,
                           precio_dije=dije)


@app.route("/reservar", methods=["GET", "POST"])
def reservar():
    precios, deco, dije = obtener_precios()
    if request.method == "POST":
        captura_nombre = None
        try:
            cliente = request.form["cliente"].strip()
            telefono = request.form.get("telefono", "").strip()
            fecha = request.form["fecha"]
            horario = request.form["horario"]
            servicio = request.form["servicio"]
            deco_n = int(request.form.get("deco_3d") or 0)
            dijes_n = int(request.form.get("dijes") or 0)

            if not cliente:
                raise ValueError("Falta el nombre.")
            if servicio not in precios:
                raise ValueError("Servicio inválido.")

            archivo = request.files.get("captura")
            if not archivo or archivo.filename == "":
                raise ValueError("Tenés que subir la captura de la transferencia para reservar.")

            captura_nombre = guardar_captura(archivo)

            turno = crear_turno(cliente, telefono, fecha, horario,
                                servicio, deco_n, dijes_n,
                                captura=captura_nombre)
            senia = calcular_senia(turno["total"])

            # 1) Generar PDF (necesario antes de los SMS)
            try:
                generar_ticket_pdf(turno)
            except Exception as e:
                print("Error PDF:", e)

            # 2) SMS ELIMINADOS (se envían por WhatsApp manualmente desde el cliente)
            # try:
            #     enviar_sms_reserva_hermana(turno, senia)
            # except Exception as e:
            #     print("Error SMS hermana:", e)
            #
            # try:
            #     enviar_sms_reserva_cliente(turno, senia)
            # except Exception as e:
            #     print("Error SMS cliente:", e)

            return render_template("confirmacion.html",
                                   nombre=NOMBRE_NEGOCIO,
                                   turno=turno,
                                   senia=senia)
        except ValueError as e:
            flash(str(e), "error")

    fecha_sel = request.args.get("fecha", datetime.now().strftime("%Y-%m-%d"))
    ocupados = horarios_ocupados(fecha_sel)
    return render_template("reservar.html",
                           nombre=NOMBRE_NEGOCIO,
                           servicios=precios,
                           precio_deco=deco,
                           precio_dije=dije,
                           horarios=HORARIOS,
                           ocupados=ocupados,
                           fecha_sel=fecha_sel,
                           alias=ALIAS, cbu=CBU,
                           titular=TITULAR, banco=BANCO,
                           porcentaje_senia=int(PORCENTAJE_SENIA * 100))


@app.route("/api/horarios/<fecha>")
def api_horarios(fecha):
    return {"ocupados": horarios_ocupados(fecha)}


@app.route("/ticket/<token>")
def ver_ticket(token):
    """Sirve el PDF del ticket usando el token del turno (link seguro)."""
    turno = obtener_turno_por_token(token)
    if not turno:
        return "Ticket no encontrado", 404

    nombre_pdf = f"{token}.pdf"
    ruta_pdf = os.path.join(TICKETS_DIR, nombre_pdf)
    if not os.path.exists(ruta_pdf):
        return "Ticket no disponible", 404

    return send_from_directory(TICKETS_DIR, nombre_pdf, mimetype="application/pdf")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pwd = request.form["password"]
        if verificar_password(pwd):
            session["admin"] = True
            return redirect(url_for("admin_turnos"))
        flash("Contraseña incorrecta", "error")
    return render_template("login_admin.html", nombre=NOMBRE_NEGOCIO)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


def requiere_admin():
    return session.get("admin") is True


@app.route("/admin/turnos")
def admin_turnos():
    if not requiere_admin():
        return redirect(url_for("admin_login"))
    fecha = request.args.get("fecha")
    turnos = listar_turnos(fecha)
    return render_template("admin_turnos.html",
                           nombre=NOMBRE_NEGOCIO,
                           turnos=turnos,
                           fecha=fecha or "")


@app.route("/admin/cancelar/<int:tid>", methods=["POST"])
def admin_cancelar(tid):
    if not requiere_admin():
        return redirect(url_for("admin_login"))
    cancelar_turno(tid)
    flash("Turno cancelado", "ok")
    return redirect(url_for("admin_turnos"))


@app.route("/admin/pagado/<int:tid>", methods=["POST"])
def admin_pagado(tid):
    if not requiere_admin():
        return redirect(url_for("admin_login"))
    marcar_pagado(tid, 1)
    flash("Turno marcado como pagado", "ok")
    return redirect(url_for("admin_turnos"))


@app.route("/admin/ganancias")
def admin_ganancias():
    if not requiere_admin():
        return redirect(url_for("admin_login"))
    total, cant = calcular_ganancias()
    por_mes = ganancias_por_mes()
    return render_template("admin_ganancias.html",
                           nombre=NOMBRE_NEGOCIO,
                           total=total, cant=cant, por_mes=por_mes)


@app.route("/admin/precios", methods=["GET", "POST"])
def admin_precios():
    if not requiere_admin():
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        for key, val in request.form.items():
            if key.startswith("precio::") or key in ("precio_deco_3d", "precio_dije"):
                try:
                    guardar_config(key, int(val))
                except ValueError:
                    pass
        flash("Precios actualizados", "ok")
        return redirect(url_for("admin_precios"))

    precios, deco, dije = obtener_precios()
    return render_template("admin_precios.html",
                           nombre=NOMBRE_NEGOCIO,
                           servicios=precios,
                           precio_deco=deco,
                           precio_dije=dije)


@app.route("/capturas/<filename>")
def ver_captura(filename):
    if not requiere_admin():
        return redirect(url_for("admin_login"))
    return send_from_directory(CAPTURAS_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)