import io
import base64
import qrcode
import weasyprint

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required

from .models import Ingreso


import io
import base64
import qrcode
import weasyprint

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required

from .models import MovimientoFinanciero

# sba/views.py
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

@staff_member_required
def manual_usuario_view(request):
    context = {
        **admin.site.each_context(request),  # Mantiene el contexto global del admin (barra lateral, usuario, etc.)
        "title": "Manual de Usuario y Operación",
        "modulo": "SmartBusinessAnalytics",
    }
    return render(request, "admin/sba/manual_usuario.html", context)



@staff_member_required
def pdf_reporte_movimiento(request, pk):
    # Obtener el movimiento financiero por su pk
    movimiento = get_object_or_404(MovimientoFinanciero, pk=pk)

    # ==============================
    # GENERAR QR
    # ==============================
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=4
    )

    # Datos para el QR: Se incluyen los campos relevantes del movimiento
    qr_data = (
        f"REPORTE-MOVIMIENTO | {movimiento.codigo_referencia} | "
        f"{movimiento.fecha_devengo} | "
        f"{movimiento.contraparte_nombre} | "
        f"Categoría: {movimiento.get_categoria_display()} | "
        f"Monto Neto: {movimiento.monto_neto}"
    )

    # Añadir los datos al QR
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Crear imagen del QR
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    # Convertir la imagen a base64
    qr_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    # ==============================
    # RENDER HTML
    # ==============================
    # Renderizar el HTML para el reporte, pasando los datos necesarios
    html = render_to_string(
        "movimiento_financiero/pdf_reporte_movimiento.html",
        {
            "movimiento": movimiento,
            "qr_url": qr_url,
        }
    )

    # ==============================
    # RESPONSE PDF
    # ==============================
    # Configurar la respuesta HTTP para devolver el archivo PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="ReporteMovimiento_{movimiento.codigo_referencia}.pdf"'
    )

    # Crear el PDF con WeasyPrint, generando el archivo PDF a partir del HTML
    weasyprint.HTML(
        string=html,
        base_url=request.build_absolute_uri()
    ).write_pdf(
        response,
        stylesheets=[
            weasyprint.CSS("smartbusinessanalytics/static/css/pdf.css")  # Ruta al archivo CSS para estilos
        ],
        presentational_hints=True
    )

    return response


@staff_member_required
def pdf_reporte_ingreso(request, pk):
    ingreso = get_object_or_404(Ingreso, pk=pk)

    # ==============================
    # GENERAR QR
    # ==============================
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=4
    )

    qr_data = (
        f"REPORTE-INGRESO | {ingreso.codigo_referencia} | "
        f"{ingreso.fecha_devengo} | "
        f"{ingreso.cliente_nombre} | "
        f"{ingreso.monto_neto}"
    )

    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    qr_url = (
        f"data:image/png;base64,"
        f"{base64.b64encode(buffer.getvalue()).decode()}"
    )

    # ==============================
    # RENDER HTML
    # ==============================
    html = render_to_string(
        "ingresos/pdf_reporte_ingresos.html",
        {
            "ingreso": ingreso,
            "qr_url": qr_url,
        }
    )

    # ==============================
    # RESPONSE PDF
    # ==============================
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="ReporteIngreso_'
        f'{ingreso.codigo_referencia}.pdf"'
    )

    weasyprint.HTML(
        string=html,
        base_url=request.build_absolute_uri()
    ).write_pdf(
        response,
        stylesheets=[
            weasyprint.CSS(
                "smartbusinesslaw/static/css/pdf.css"
            )
        ],
        presentational_hints=True
    )

    return response


import io
import base64
import qrcode
import weasyprint

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required

from .models import Egreso







@staff_member_required
def pdf_reporte_egreso(request, pk):
    egreso = get_object_or_404(Egreso, pk=pk)

    # ==============================
    # GENERAR QR
    # ==============================
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=4
    )

    qr_data = (
        f"REPORTE-EGRESO | {egreso.codigo_referencia} | "
        f"{egreso.fecha_devengo} | "
        f"{egreso.proveedor_nombre} | "
        f"{egreso.monto_neto}"
    )

    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    qr_url = (
        f"data:image/png;base64,"
        f"{base64.b64encode(buffer.getvalue()).decode()}"
    )

    # ==============================
    # RENDER HTML
    # ==============================
    html = render_to_string(
        "egresos/pdf_reporte_egresos.html",
        {
            "egreso": egreso,
            "qr_url": qr_url,
        }
    )

    # ==============================
    # RESPONSE PDF
    # ==============================
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="ReporteEgreso_'
        f'{egreso.codigo_referencia}.pdf"'
    )

    weasyprint.HTML(
        string=html,
        base_url=request.build_absolute_uri()
    ).write_pdf(
        response,
        stylesheets=[
            weasyprint.CSS(
                "smartbusinesslaw/static/css/pdf.css"
            )
        ],
        presentational_hints=True
    )

    return response


import io
import base64
import qrcode
import weasyprint

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required

from .models import EstadoFinanciero


@staff_member_required
def pdf_reporte_financiero(request, pk):
    estado = get_object_or_404(EstadoFinanciero, pk=pk)

    # ==============================
    # GENERAR QR
    # ==============================
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=4
    )

    qr_data = (
        f"ANALISIS-FINANCIERO | {estado.fecha_inicio} a {estado.fecha_fin} | "
        f"Total Ingresos: {estado.total_ingresos} | "
        f"Total Egresos: {estado.total_egresos} | "
        f"Utilidad Neta: {estado.utilidad_neta}"
    )

    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    qr_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    # ==============================
    # OBTENER DETALLE DE INGRESOS Y EGRESOS
    # ==============================
    ingresos = Ingreso.objects.filter(
        fecha_devengo__gte=estado.fecha_inicio,
        fecha_devengo__lte=estado.fecha_fin
    ).order_by('fecha_devengo')

    egresos = Egreso.objects.filter(
        fecha_devengo__gte=estado.fecha_inicio,
        fecha_devengo__lte=estado.fecha_fin
    ).order_by('fecha_devengo')

    # ==============================
    # CALCULAR SUBTOTALES Y UTILIDADES
    # ==============================
    subtotal_ingresos = sum([i.monto_neto for i in ingresos if i.monto_neto])
    subtotal_egresos = sum([e.monto_neto for e in egresos if e.monto_neto])

    utilidad_bruta = estado.utilidad_bruta
    utilidad_neta = estado.utilidad_neta

    # ==============================
    # RENDER HTML
    # ==============================
    html = render_to_string(
        "finanzas/pdf_reporte_financiero.html",
        {
            "estado": estado,
            "qr_url": qr_url,
            "ingresos": ingresos,
            "egresos": egresos,
            "subtotal_ingresos": subtotal_ingresos,
            "subtotal_egresos": subtotal_egresos,
            "utilidad_bruta": utilidad_bruta,
            "utilidad_neta": utilidad_neta,
            "margen_bruto": estado.margen_utilidad_bruta,
            "margen_neto": estado.margen_utilidad_neta,
            "rentabilidad": estado.rentabilidad,
            "liquidez": estado.liquidez,
        }
    )

    # ==============================
    # RESPONSE PDF
    # ==============================
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="ReporteFinanciero_'
        f'{estado.fecha_inicio}_{estado.fecha_fin}.pdf"'
    )

    weasyprint.HTML(
        string=html,
        base_url=request.build_absolute_uri()
    ).write_pdf(
        response,
        stylesheets=[weasyprint.CSS("smartbusinesslaw/static/css/pdf.css")],
        presentational_hints=True
    )

    return response
