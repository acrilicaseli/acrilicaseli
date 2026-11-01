import os
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from servicios import NOMBRE_NEGOCIO, TICKETS_DIR

LOGO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static", "logo.png"
)


def _dibujar_logo_circular(c, cx, cy, radio):
    """Dibuja el logo recortado en círculo, centrado en (cx, cy)."""
    if not os.path.exists(LOGO_PATH):
        print("Logo no encontrado en:", LOGO_PATH)
        return False
    try:
        c.saveState()
        p = c.beginPath()
        p.circle(cx, cy, radio)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(
            ImageReader(LOGO_PATH),
            cx - radio, cy - radio,
            width=radio * 2, height=radio * 2,
            mask='auto', preserveAspectRatio=True
        )
        c.restoreState()
        c.setStrokeColorRGB(0.83, 0.68, 0.21)
        c.setLineWidth(1.2)
        c.circle(cx, cy, radio)
        return True
    except Exception as e:
        print("Error logo PDF:", e)
        return False


def generar_ticket_pdf(turno):
    """Genera el PDF usando el token como nombre de archivo (seguro para URL)."""
    os.makedirs(TICKETS_DIR, exist_ok=True)

    token = turno.get("token") or f"tmp_{turno['id']}"
    ruta = os.path.join(TICKETS_DIR, f"{token}.pdf")

    c = canvas.Canvas(ruta, pagesize=A6)
    ancho, alto = A6
    y = alto - 30

    # Logo circular
    radio = 26
    if _dibujar_logo_circular(c, ancho / 2, y - radio, radio):
        y -= radio * 2 + 10

    # Encabezado
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(ancho / 2, y, NOMBRE_NEGOCIO)
    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(ancho / 2, y, "TICKET DE RESERVA")
    y -= 25

    # Datos
    c.setFont("Helvetica", 10)
    lineas = [
        f"Cliente : {turno['cliente']}",
        f"Telefono: {turno.get('telefono') or '-'}",
        f"Fecha   : {turno['fecha']}",
        f"Horario : {turno['horario']}",
        f"Servicio: {turno['servicio']}",
    ]
    if turno.get("deco_3d"):
        lineas.append(f"Deco 3D : {turno['deco_3d']} unas")
    if turno.get("dijes"):
        lineas.append(f"Dijes   : {turno['dijes']}")

    for linea in lineas:
        c.drawString(30, y, linea)
        y -= 16

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, y, f"TOTAL: ${turno['total']:,}".replace(",", "."))
    y -= 16

    if turno.get("senia"):
        c.setFont("Helvetica", 10)
        c.drawString(30, y, f"Sena abonada: ${turno['senia']:,}".replace(",", "."))
        y -= 16
        saldo = turno["total"] - turno["senia"]
        c.drawString(30, y, f"Saldo: ${saldo:,}".replace(",", "."))
        y -= 16

    y -= 14
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(ancho / 2, y, "Gracias por tu reserva!")
    c.save()
    return ruta