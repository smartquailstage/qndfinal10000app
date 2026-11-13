from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Ingreso
from django.template.loader import render_to_string
from unfold.components import BaseComponent, register_component
import csv
import xlsxwriter
from django.http import HttpResponse
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import (
    ExportForm,
    ImportForm,
    SelectableFieldsExportForm,
)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SesionCaja, EstadoFinanciero, MovimientoFinanciero # (y tus demás modelos)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User  # Importa tu modelo personalizado

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User



@admin.register(User)
class CustomUserAdmin(UserAdmin,ModelAdmin):
    # Columnas que se ven en la tabla general de usuarios
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "avatar")
    
    # Campos por los que se puede buscar
    search_fields = ("username", "first_name", "last_name", "email")
    
    # Filtros laterales
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")

    # Estructura de la vista de edición/detalle de un usuario específico
    fieldsets = UserAdmin.fieldsets + (
        ("Información Personalizada", {
            "fields": ("avatar",),
        }),
    )

    # Estructura para la vista de creación de un nuevo usuario desde el admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Información Personalizada", {
            "fields": ("avatar",),
        }),
    )


admin.site.site_header = "SmartBusinessAnalytics"
admin.site.site_title = "SmartBusinessAnalytics"
admin.site.index_title = "Smart Business Analytics"

# sba/admin.py
import json
from .models import EstadoFinanciero, MovimientoFinanciero






def dashboard_callback(request, context):
    # 1. Obtenemos todas las fechas disponibles para poblar el selector en la UI
    fechas_disponibles = EstadoFinanciero.objects.order_by("-fecha_fin").values_list('fecha_fin', flat=True)
    
    # 2. Capturamos la fecha seleccionada desde los parámetros GET (?fecha_estado=...)
    fecha_seleccionada = request.GET.get('fecha_estado')
    
    if fecha_seleccionada:
        estado = EstadoFinanciero.objects.filter(fecha_fin=fecha_seleccionada).first()
    else:
        # Por defecto tomamos el más reciente
        estado = EstadoFinanciero.objects.order_by("-fecha_fin").first()

    # 3. Datos para el gráfico de distribución de ingresos (Pie)
    ingresos_qs = MovimientoFinanciero.objects.filter(es_ingreso=True)
    ventas = float(sum(m.monto_neto.amount for m in ingresos_qs.filter(categoria_ingresos="ventas") if m.monto_neto))
    inversion = float(sum(m.monto_neto.amount for m in ingresos_qs.filter(categoria_ingresos="inversion") if m.monto_neto))
    acciones = float(sum(m.monto_neto.amount for m in ingresos_qs.filter(categoria_ingresos="acciones_legales") if m.monto_neto))
    deducciones = float(sum(m.monto_neto.amount for m in ingresos_qs.filter(categoria_ingresos="deducciones") if m.monto_neto))

    chart_ingresos = {
        "labels": ["Ventas", "Inversión", "Acciones Legales", "Deducciones"],
        "datasets": [{
            "data": [ventas, inversion, acciones, deducciones],
            "backgroundColor": [
                "var(--color-primary-900)",
                "var(--color-primary-700)",
                "var(--color-primary-500)",
                "var(--color-primary-300)"
            ]
        }]
    }

    # 4. Datos seguros para el gráfico de Radar (Métricas Operativas)
    if estado:
        m_bruto = float(estado.margen_utilidad_bruta or 0)
        m_neto = float(estado.margen_utilidad_neta or 0)
        rentabilidad = float(estado.rentabilidad or 0)
        nrr = float(estado.nrr or 0)
        gross_margin = float(estado.gross_margin_porcentaje or 0)
        cobertura = float(estado.ratio_cobertura or 0)
    else:
        m_bruto = m_neto = rentabilidad = nrr = gross_margin = cobertura = 0.0

    chart_radar = {
        "labels": ["M. Bruto", "M. Neto", "Rentabilidad", "NRR", "Gross Margin", "Cobertura"],
        "datasets": [{
            "data": [m_bruto, m_neto, rentabilidad, nrr, gross_margin, cobertura],
            "backgroundColor": "oklch(55.1% .027 264.364 / 10%)",
            "borderWidth": 2,
            "borderColor": "var(--color-primary-700)"
        }]
    }

    # 5. Cálculo y normalización exacta al 100% para la barra unificada de márgenes
    if estado:
        b = float(estado.margen_utilidad_bruta or 0)
        n = float(estado.margen_utilidad_neta or 0)
        r = float(estado.rentabilidad or 0)
        
        suma_total = b + n + r
        if suma_total > 0:
            p_bruto = round((b / suma_total) * 100, 2)
            p_neto = round((n / suma_total) * 100, 2)
            # El último elemento absorbe cualquier residuo decimal para clavar el 100% exacto
            p_rentabilidad = round(100.0 - (p_bruto + p_neto), 2)
        else:
            p_bruto = p_neto = p_rentabilidad = 0
    else:
        b = n = r = p_bruto = p_neto = p_rentabilidad = 0

    context.update({
        "modulo": "SBA - Finanzas y Analítica",
        "estado": estado,
        "fechas_disponibles": fechas_disponibles,
        "fecha_seleccionada": str(fecha_seleccionada) if fecha_seleccionada else "",
        "grafico_ingresos_json": json.dumps(chart_ingresos),
        "grafico_radar_json": json.dumps(chart_radar),
        "barra_metrics": {
            "bruto_val": b,
            "neto_val": n,
            "rentabilidad_val": r,
            "bruto_pct": p_bruto,
            "neto_pct": p_neto,
            "rentabilidad_pct": p_rentabilidad,
        }
    })
    return context

def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={opts.verbose_name}.csv'
    writer = csv.writer(response)

    # Solo campos concretos del modelo
    fields = [field for field in opts.fields if not field.many_to_many and not field.one_to_many]

    # Escribir encabezados
    writer.writerow([field.verbose_name for field in fields])

    # Escribir datos
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime):
                value = value.strftime('%d/%m/%Y')
            data_row.append(value)
        writer.writerow(data_row)

    return response

export_to_csv.short_description = 'Exportar a CSV'


def export_to_excel(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={opts.verbose_name_plural}.xlsx'

    # xlsxwriter requiere un objeto tipo archivo (BytesIO)
    import io
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Solo campos concretos del modelo
    fields = [field for field in opts.fields if not field.many_to_many and not field.one_to_many]

    # Escribir encabezados
    for i, field in enumerate(fields):
        worksheet.write(0, i, field.verbose_name)

    # Escribir datos
    for row_num, obj in enumerate(queryset, start=1):
        for col_num, field in enumerate(fields):
            value = getattr(obj, field.name)
            if isinstance(value, datetime):
                value = value.strftime('%d/%m/%Y')
            worksheet.write(row_num, col_num, str(value))  # Convertir a string

    workbook.close()
    output.seek(0)
    response.write(output.read())

    return response

export_to_excel.short_description = 'Exportar a Excel'



def REPORTE_MOVIMIENTO_FINANCIERO_PDF(obj):
    # Genera la URL del reporte PDF usando el reverse y el ID del objeto
    url = reverse("sba:pdf_reporte_movimiento_financiero", args=[obj.pk])
    
    # Retorna un enlace que abrirá el PDF en una nueva pestaña
    return mark_safe(
        f'<a href="{url}" target="_blank">'
        f'<span class="material-symbols-outlined">download</span> '
        f'Reporte de Movimiento Financiero</a>'
    )

REPORTE_MOVIMIENTO_FINANCIERO_PDF.short_description = "Reporte de Movimiento Financiero"



import io
import base64
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
from calendar import monthrange

from unfold.components import BaseComponent, register_component
from django.template.loader import render_to_string

from .models import MovimientoFinanciero


from django.db.models import Sum
from django.template.loader import render_to_string
from decimal import Decimal
from .models import MovimientoFinanciero


@admin.action(description="Duplicar Balance Financiero")
def duplicar_balances(modeladmin, request, queryset):
    for obj in queryset:

        related_data = []

        # 🔍 Detectar automáticamente TODOS los inlines reales
        for rel in obj._meta.related_objects:
            accessor = rel.get_accessor_name()
            try:
                items = list(getattr(obj, accessor).all())
                related_data.append((rel, items))
            except Exception:
                continue  # evita errores tipo "no existe"

        # 🧬 Clonar padre
        obj.pk = None
        obj.save()

        # 🔁 Clonar hijos
        for rel, items in related_data:
            for item in items:
                item.pk = None

                # encontrar el FK correcto dinámicamente
                for field in item._meta.fields:
                    if isinstance(field, models.ForeignKey) and field.related_model == obj.__class__:
                        setattr(item, field.name, obj)

                item.save()




@register_component
class MovimientoFinancieroResumenComponentDemo(BaseComponent):
    template_name = "admin/movimientos.html"
    name = "Resumen Movimiento Financiero"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):

        iva_ingresos = (
            MovimientoFinanciero.objects
            .filter(es_ingreso=True)
            .aggregate(total=Sum("iva"))["total"]
            or Decimal("0.00")
        )

        iva_egresos = (
            MovimientoFinanciero.objects
            .filter(es_egreso=True)
            .aggregate(total=Sum("iva"))["total"]
            or Decimal("0.00")
        )

        iva_por_pagar = iva_ingresos - iva_egresos

        cards = [
            {
                "title": "IVA Ingresos",
                "value": float(iva_ingresos),
                "badge": "USD",
                "badge_color": "success",
            },
            {
                "title": "IVA Egresos",
                "value": float(iva_egresos),
                "badge": "USD",
                "badge_color": "warning",
            },
            {
                "title": "IVA por Pagar",
                "value": float(iva_por_pagar),
                "badge": "USD",
                "badge_color": "success" if iva_por_pagar >= 0 else "danger",
                "footer": "Ingresos - Egresos",
            },
        ]

        return {
            "title": "Resumen IVA Global",
            "cards": cards,
        }

    def render(self):
        return render_to_string(
            self.template_name,
            self.get_context_data(),
            request=self.request
        )

from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import MovimientoFinanciero


@admin.register(MovimientoFinanciero)
class MovimientoFinancieroAdmin(ModelAdmin,ImportExportModelAdmin):
    # ----------------------------------
    # Componentes visuales
    # ----------------------------------
    list_sections = [
        MovimientoFinancieroResumenComponentDemo,
    ]

    actions =[
    duplicar_balances,
    export_to_csv,
    export_to_excel,

    ]

    import_form_class = ImportForm
    export_form_class = ExportForm


    # ----------------------------------
    # Fieldsets en tabs
    # ----------------------------------
    fieldsets = (
        ("I. Información General", {
            "fields": (
                "es_ingreso",
                "es_egreso",
                "categoria_ingresos",
                "categoria",
                "fecha_devengo",
                "codigo_referencia",
                "descripcion",
                "contraparte_nombre",
                "contraparte_identificacion_fiscal",
                "confirmado",
            ),
            'classes': ('collapse',),
        }),

        ("II. Detalle", {
            "fields": (
                "monto_bruto",
                "descuento",
                "tasa_iva",
                "costo_directo",
                "gastos_indirectos",
            ),
           'classes': ('collapse',),
        }),

        ("IV. Resultados Calculados", {
            "fields": (
                "base_imponible",
                "iva",
                "monto_neto",
                "utilidad_bruta",
                "utilidad_neta",
            ),
         'classes': ('collapse',),
        }),

        ("V. Metadatos", {
            "fields": (
                "hash_registro",
                "created_at",
                "fecha_registro",
            ),
          'classes': ('collapse',),
        }),
    )

    # ----------------------------------
    # Listado en admin
    # ----------------------------------
    conditional_fields = {

    "categoria_ingresos": "es_ingreso",

    # Se muestra si es egreso
    "categoria": "es_egreso",
   
    }



    list_display = (
        "fecha_devengo",
        "tipo_movimiento",
        "categoria",
        "monto_principal",
        "utilidad_neta",
        "confirmado",
    )

    list_filter = (
        "es_ingreso",
        "es_egreso",
        "categoria",
        "fecha_devengo",
        "confirmado",
    )

    search_fields = (
        "codigo_referencia",
        "descripcion",
        "contraparte_nombre",
        "contraparte_identificacion_fiscal",
    )

    readonly_fields = (
        "hash_registro",
        "base_imponible",
        "iva",
        "monto_neto",
        "utilidad_bruta",
        "utilidad_neta",
        "created_at",
        "fecha_registro",
    )

    unfold_fieldsets = True

    # ----------------------------------
    # Campos calculados para listado
    # ----------------------------------
    def tipo_movimiento(self, obj):
        return "Ingreso" if obj.es_ingreso else "Egreso"
    tipo_movimiento.short_description = "Tipo"

    def monto_principal(self, obj):
        return obj.monto_neto
    monto_principal.short_description = "Monto Neto"


# ----------------------------------
    # Filtro de seguridad por usuario (I+D Core)
    # ----------------------------------
    def get_queryset(self, request):
        """
        Filtra el listado para que los usuarios comunes solo vean sus datos,
        mientras que los superusuarios mantienen el control total del holding.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # Suponiendo que tu campo en el modelo se llama 'usuario' o 'owner'
        return qs.filter(usuario=request.user)

    def save_model(self, request, obj, form, change):
        """
        Asigna automáticamente el usuario logueado como propietario 
        del registro al momento de la creación.
        """
        if not change: # Si el registro es nuevo
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        """
        Si agregas el campo 'usuario' a los fieldsets, este método asegura 
        que nadie pueda alterarlo de forma manual, blindando el rastro de auditoría.
        """
        fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            return list(fields) + ["usuario"]
        return fields

# ------------------------------------------------------------
    # Permisos Nativos Forzados para Staff Activo (Gobernanza Automatizada)
    # ------------------------------------------------------------

    def has_module_permission(self, request):
        """
        Le dice a Django que este usuario SÍ tiene permitido ver 
        el contenedor global de la aplicación en el Admin.
        """
        return request.user.is_authenticated and request.user.is_staff and request.user.is_active

    def has_view_permission(self, request, obj=None):
        """Permite ver el listado si es staff activo."""
        return request.user.is_authenticated and request.user.is_staff and request.user.is_active

    def has_add_permission(self, request):
        """Permite crear registros si es staff activo."""
        return request.user.is_authenticated and request.user.is_staff and request.user.is_active

    def has_change_permission(self, request, obj=None):
        """Permite editar sus propios registros (get_queryset ya aislará el objeto)."""
        return request.user.is_authenticated and request.user.is_staff and request.user.is_active

    def has_delete_permission(self, request, obj=None):
        """Bloquea el borrado a usuarios comunes si lo deseas, o pon True si pueden borrar lo suyo."""
        if request.user.is_superuser:
            return True
        return False # Por seguridad en el histórico del holding



    # ----------------------------------
    # Media JS para ocultar tabs dinámicamente según tipo de movimiento
    # ----------------------------------
    class Media:
        js = ('admin/js/movimiento_financiero_toggle.js',)




def REPORTE_INGRESO_PDF(obj):
    url = reverse("sba:pdf_reporte_ingreso", args=[obj.id])
    return mark_safe(
        f'<a href="{url}" target="_blank">'
        f'<span class="material-symbols-outlined">download</span> '
        f'Reporte de Ingreso</a>'
    )


REPORTE_INGRESO_PDF.short_description = "Reporte de Ingreso"



@register_component
class IngresoIdentificacionComponentDemo(BaseComponent):
    template_name = "admin/profile_card.html"
    name = "Identificación del Ingreso"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):
        i = self.instance
        rows = [
            ["Código de referencia", i.codigo_referencia],
            ["Tipo de ingreso", i.get_tipo_ingreso_display()],
            ["Producto / Servicio", i.producto_servicio],
            ["Fecha de devengo", i.fecha_devengo],
        ]
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Identificación del Ingreso",
            "table": {"headers": ["Campo", "Detalle"], "rows": rows}
        })
        return context

    def render(self):
        return render_to_string(self.template_name, self.get_context_data())




@register_component
class ClienteIngresoComponentDemo(BaseComponent):
    template_name = "admin/profile_card.html"
    name = "Cliente"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):
        i = self.instance
        rows = [
            ["Cliente", i.cliente_nombre],
            ["Identificación fiscal", i.cliente_identificacion_fiscal or "No registrada"],
        ]
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Cliente",
            "table": {"headers": ["Campo", "Detalle"], "rows": rows}
        })
        return context

    def render(self):
        return render_to_string(self.template_name, self.get_context_data())


@register_component
class TributacionIngresoComponentDemo(BaseComponent):
    template_name = "admin/profile_card.html"
    name = "Detalle Tributario"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):
        i = self.instance
        rows = [
            ["Monto bruto", i.monto_bruto],
            ["Descuento", i.descuento],
            ["Base imponible", i.base_imponible],
            ["Tasa IVA", f"{i.tasa_iva * 100}%"],
            ["IVA", i.iva],
            ["Monto neto", i.monto_neto],
        ]
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Detalle Tributario",
            "table": {"headers": ["Campo", "Detalle"], "rows": rows}
        })
        return context

    def render(self):
        return render_to_string(self.template_name, self.get_context_data())


@register_component
class UtilidadesIngresoComponentDemo(BaseComponent):
    template_name = "admin/profile_card.html"
    name = "Utilidades"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):
        i = self.instance
        rows = [
            ["Costo del producto", i.costo_producto],
            ["Gastos asociados", i.gastos_asociados],
            ["Utilidad bruta", i.utilidad_bruta],
            ["Utilidad neta", i.utilidad_neta],
        ]
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Costos y Utilidades",
            "table": {"headers": ["Campo", "Detalle"], "rows": rows}
        })
        return context

    def render(self):
        return render_to_string(self.template_name, self.get_context_data())


@register_component
class CobroIngresoComponentDemo(BaseComponent):
    template_name = "admin/profile_card.html"
    name = "Cobro"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):
        i = self.instance
        rows = [
            ["Método de pago", i.get_metodo_pago_display()],
            ["Cobrado", "Sí" if i.cobrado else "No"],
            ["Fecha de cobro", i.fecha_cobro or "Pendiente"],
        ]
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Información Bancaria",
            "table": {"headers": ["Campo", "Detalle"], "rows": rows}
        })
        return context

    def render(self):
        return render_to_string(self.template_name, self.get_context_data())






from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from unfold.admin import ModelAdmin
from .models import EstadoFinanciero



# ================================
# Objeto PDF para Admin
# ================================
def REPORTE_FINANCIERO_PDF(obj):
    url = reverse("sba:pdf_reporte_financiero", args=[obj.id])
    return mark_safe(
        f'<a href="{url}" target="_blank">'
        f'<span class="material-symbols-outlined">download</span> '
        f'Reporte Financiero</a>'
    )

REPORTE_FINANCIERO_PDF.short_description = "Reporte Financiero"



@register_component
class EstadoPeriodoComponentDemo(BaseComponent):
    template_name = "admin/profile_card.html"
    name = "Período Analizado"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):
        e = self.instance
        rows = [
            ["Fecha inicio", e.fecha_inicio],
            ["Fecha fin", e.fecha_fin],
        ]
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Período Financiero",
            "table": {"headers": ["Campo", "Detalle"], "rows": rows},
        })
        return context

    def render(self):
        return render_to_string(self.template_name, self.get_context_data())

import json
from datetime import datetime
from django.template.loader import render_to_string



import io
import base64
from datetime import datetime, date
from calendar import monthrange
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from django.template.loader import render_to_string

import io
import base64
from datetime import datetime
from calendar import monthrange

import numpy as np
import matplotlib.pyplot as plt
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

import io
import base64
from datetime import datetime
from calendar import monthrange

import numpy as np
import matplotlib.pyplot as plt

from django.template.loader import render_to_string
from django.contrib import admin
from django.db.models import Sum



import io
import base64
from datetime import datetime
from calendar import monthrange

import numpy as np
import matplotlib.pyplot as plt

from django.template.loader import render_to_string
from datetime import datetime, timedelta

import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
from calendar import monthrange
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
from calendar import monthrange
from django.template.loader import render_to_string
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
from calendar import monthrange
from django.template.loader import render_to_string

import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from calendar import monthrange
from django.template.loader import render_to_string
from unfold.components import BaseComponent, register_component
from .models import Ingreso, Egreso

import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from calendar import monthrange
from django.template.loader import render_to_string
from unfold.components import BaseComponent, register_component
from .models import Ingreso, Egreso
import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from calendar import monthrange
from django.template.loader import render_to_string
from unfold.components import BaseComponent, register_component
from .models import Ingreso, Egreso

from djmoney.money import Money

import io
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Asegura estabilidad en entornos de servidores web
import matplotlib.pyplot as plt
from datetime import datetime
from calendar import monthrange
from django.db.models import Max
from django.template.loader import render_to_string
from unfold.components import BaseComponent, register_component
# Asegúrate de tener importado Money y tu modelo según tu arquitectura:
# from djmoney.money import Money 




@register_component
class EstadoResumenContableComponentDemo(BaseComponent):
    template_name = "admin/banner.html"
    name = "Resumen Contable"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):
        e = self.instance
        context = super().get_context_data(**kwargs)

        # Si no hay instancia del estado resumen, retornamos un contexto limpio
        if not e:
            context["sin_datos"] = True
            return context

        # ==========================
        # Helper seguro para conversión de tipos
        # ==========================
        def money_to_float(m):
            # Si el entorno usa djmoney, extrae la propiedad .amount nativa de la moneda
            if hasattr(m, 'amount'):
                return float(m.amount)
            # Manejo de objetos Money customizados según tu importación anterior
            if m.__class__.__name__ == 'Money':
                return float(m.amount)
            return float(m or 0.0)

        # ==========================
        # Extracción y Validación de Fechas
        # ==========================
        start = e.fecha_inicio
        end = e.fecha_fin
        
        if not start or not end:
            context["sin_datos"] = True
            return context

        if isinstance(start, datetime):
            start = start.date()
        if isinstance(end, datetime):
            end = end.date()

        # ==========================
        # CONTROL PREVENTIVO: Validación del Árbol de Datos
        # ==========================
        ingresos_qs = MovimientoFinanciero.objects.filter(
            fecha_devengo__range=(start, end),
            es_ingreso=True
        )
        if not self.request.user.is_superuser:
            ingresos_qs = ingresos_qs.filter(usuario=self.request.user)

        egresos_qs = MovimientoFinanciero.objects.filter(
            fecha_devengo__range=(start, end),
            es_egreso=True
        )
        if not self.request.user.is_superuser:
            egresos_qs = egresos_qs.filter(usuario=self.request.user)

        # Si ambos querysets están vacíos, activamos el escudo preventivo y evitamos caer en Matplotlib
        if not ingresos_qs.exists() and not egresos_qs.exists():
            context.update({
                "title": "Resumen Contable",
                "sin_datos": True,
                "chart_image": "",
                "scatter_chart_image": "",
                "pie_chart_image": "",
                "table": {"headers": ["Campo", "Detalle"], "rows": [["Fecha inicio", start], ["Fecha fin", end]]},
                "header_stats": [],
                "cards": [],
                "gastos": [],
                "ingresos_corrientes": [],
                "metricas_paap": []
            })
            return context

        # ==========================
        # Construcción de Estructuras de Datos Auxiliares (Tablas y KPIs)
        # ==========================
        table_context = {
            "headers": ["Campo", "Detalle"],
            "rows": [
                ["Fecha inicio", start],
                ["Fecha fin", end],
            ],
        }

        cards = [
            {
                "title": "Efectivo Bancos",
                "value": e.total_efectivo_bancos, 
                "badge": f"Error: {e.error_conciliacion_porcentaje}%",
                "badge_color": "secondary", "nombre_banco": e.nombre_banco, 
                "footer": f"Discrepancia: {e.diferencia_ingresos}"
            },
            {"title": "Punto de Equilibrio", "value": e.punto_equilibrio, "badge": f"Liquidez:{e.ratio_cobertura}%", "badge_color": "warning"},
            {"title": "Dividendos", "value": e.dividendos_accionistas, "badge": f"Rentabilidad: {e.rentabilidad}%", "badge_color": "success"},
        ]

        header_stats = [
            {"title": "Utilidades Netas", "value": e.utilidad_neta, "badge": "Utilidades", "badge_color": "success", "porcentaje": f"{e.margen_utilidad_neta}"},
            {"title": "Ingresos", "value": e.total_ingresos, "badge": "Ingresos", "badge_color": "primary", "discrepancia": f"{e.diferencia_ingresos}"},
            {"title": "Egresos", "value": e.total_egresos, "badge": "Egresos", "badge_color": "warning", "discrepancia": f"{e.diferencia_egresos}"},
            {"title": "Fecha de inicio", "value": start, "badge": "Inicio", "badge_color": "success"},
            {"title": "Fecha de fin", "value": end, "badge": "Fin", "badge_color": "success"},
        ]

        # ==========================
        # MÉTRICAS OPERATIVAS Y PAAP (SmartBusinessPlatforms)
        # ==========================
        metricas_paap = [
            {"title": "ARPU", "value": e.arpu, "badge": "Unidad", "badge_color": "info"},
            {"title": "CAC", "value": e.cac, "badge": "Adquisición", "badge_color": "secondary"},
            {"title": "LTV", "value": e.ltv, "badge": "Valor Vida", "badge_color": "success"},
            {"title": "Ratio LTV:CAC", "value": e.ratio_ltv_cac, "badge": "Eficiencia", "badge_color": "primary"},
            {"title": "Payback Period", "value": f"{e.payback_period_meses} meses", "badge": "Recuperación", "badge_color": "warning"},
            {"title": "Churn Rate", "value": f"{e.churn_rate}%", "badge": "Bajas", "badge_color": "danger"},
            {"title": "NRR (Net Revenue Retention)", "value": f"{e.nrr}%", "badge": "Retención", "badge_color": "success"},
            {"title": "Gross Margin", "value": f"{e.gross_margin_porcentaje}%", "badge": "Margen Bruto", "badge_color": "primary"},
            {"title": "Burn Rate", "value": e.burn_rate, "badge": "Quema de Caja", "badge_color": "danger"},
            {"title": "Runway", "value": f"{e.runway_meses} meses", "badge": "Supervivencia", "badge_color": "warning"},
        ]

        raw_gastos = [
            {"title": "Gastos Fijos", "value": e.gastos_fijos},
            {"title": "Gastos Operativos", "value": e.gastos_operativos},
            {"title": "Gastos Publicitarios", "value": e.gastos_publicitarios},
            {"title": "Gastos Legales", "value": e.gastos_legales},
            {"title": "Gastos Nómina", "value": e.gastos_nomina},
            {"title": "Gastos Tributarios", "value": e.gastos_tributarios},
            {"title": "Declaración IVA", "value": e.declaracion_iva},
            {"title": "Cuentas por Pagar", "value": e.cuentas_pagar},
            {"title": "Deudas", "value": e.deudas_pagar},
        ]

        raw_ingresos = [
            {"title": "Ventas", "value": e.ventas},
            {"title": "Inversiones", "value": e.inversiones},
            {"title": "Acciones Legales", "value": e.acciones_legales},
            {"title": "Cuentas por Cobrar", "value": e.cuentas_cobrar},
            {"title": "Deducción Gastos", "value": e.deducción_gastos if hasattr(e, 'deducción_gastos') else getattr(e, 'deduccion_gastos', 0)},
        ]

        # ==========================
        # Agrupación Temporal Mensual
        # ==========================
        months, ingresos, egresos, utilidades = [], [], [], []
        current = start.replace(day=1)

        while current <= end:
            months.append(current.strftime("%b %Y"))
            last_day = monthrange(current.year, current.month)[1]
            mes_inicio = current
            mes_fin = current.replace(day=last_day)

            m_ing_qs = ingresos_qs.filter(fecha_devengo__range=(mes_inicio, mes_fin))
            m_egr_qs = egresos_qs.filter(fecha_devengo__range=(mes_inicio, mes_fin))

            ing = sum(money_to_float(i.monto_neto) for i in m_ing_qs)
            egr = sum(money_to_float(x.monto_neto) for x in m_egr_qs)
            
            ingresos.append(ing)
            egresos.append(egr)
            utilidades.append(ing - egr)

            current = current.replace(
                year=current.year + (current.month // 12),
                month=(current.month % 12) + 1,
            )

        x_vals = np.array(ingresos, dtype=float)
        y_vals = np.array(egresos, dtype=float)
        utilidades_vals = np.array(utilidades, dtype=float)

        # ==========================
        # GRÁFICO 1 – BARRAS APILADAS
        # ==========================
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        x_indexes = np.arange(len(months))
        ax1.bar(x_indexes, x_vals, color=(111/255, 207/255, 151/255, 0.75), label="Ingresos")
        ax1.bar(x_indexes, y_vals, bottom=x_vals, color=(242/255, 201/255, 76/255, 0.65), label="Egresos")
        ax1.bar(x_indexes, utilidades_vals, bottom=x_vals + y_vals, color=(79/255, 142/255, 247/255, 0.75), label="Utilidad")
        ax1.set_xticks(x_indexes)
        ax1.set_xticklabels(months, rotation=45, ha="right")
        ax1.set_ylabel("USD")
        ax1.yaxis.grid(True, linestyle="--", alpha=0.4)
        ax1.set_axisbelow(True)
        ax1.legend()
        for spine in ax1.spines.values():
            spine.set_visible(False)
        
        buffer1 = io.BytesIO()
        fig1.savefig(buffer1, format="png", dpi=100, transparent=True, bbox_inches="tight")
        plt.close(fig1)
        buffer1.seek(0)
        bar_chart = f"data:image/png;base64,{base64.b64encode(buffer1.getvalue()).decode()}"

        # ==========================
        # GRÁFICO 2 – DISPERSIÓN CON BARRAS DE ERROR
        # ==========================
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        x_bank = money_to_float(e.total_ingresos_bancos)
        y_bank = money_to_float(e.total_egresos_bancos)

        if len(x_vals) > 0 and x_vals[0] != 0:
            x_err = np.array([abs(x_bank - x_vals[0]) * 0.5])
        else:
            x_err = np.array([0.0])

        if len(y_vals) > 0 and y_vals[0] != 0:
            y_err = np.array([abs(y_bank - y_vals[0]) * 0.5])
        else:
            y_err = np.array([0.0])

        ax2.errorbar(
            x_vals, y_vals, xerr=x_err[:len(x_vals)], yerr=y_err[:len(y_vals)],
            fmt="s", markersize=8, color="#e82b0c", ecolor="#e82b0c", elinewidth=2, capsize=6, alpha=0.85
        )

        if len(x_vals) > 1 and np.std(x_vals) > 0:
            m, b = np.polyfit(x_vals, y_vals, 1)
            ax2.plot(x_vals, m * x_vals + b, "--", color="gray", linewidth=3)
            
        ax2.set_xlabel("Ingresos (USD)")
        ax2.set_ylabel("Egresos (USD)")
        ax2.grid(True, linestyle="--", alpha=0.4)
        for spine in ax2.spines.values():
            spine.set_visible(False)
            
        buffer2 = io.BytesIO()
        fig2.savefig(buffer2, format="png", dpi=100, transparent=True, bbox_inches="tight")
        plt.close(fig2)
        buffer2.seek(0)
        scatter_chart = f"data:image/png;base64,{base64.b64encode(buffer2.getvalue()).decode()}"

        # ==========================
        # GRÁFICO 3 – PIE CHART POR CATEGORÍAS
        # ==========================
        ingresos_categoria = {}
        for i in ingresos_qs:
            if i.categoria_ingresos:
                ingresos_categoria[i.categoria_ingresos] = ingresos_categoria.get(i.categoria_ingresos, 0.0) + money_to_float(i.monto_neto)

        egresos_categoria = {}
        for g in egresos_qs:
            if g.categoria:
                egresos_categoria[g.categoria] = egresos_categoria.get(g.categoria, 0.0) + money_to_float(g.monto_neto)

        ingresos_labels = list(ingresos_categoria.keys())
        ingresos_values = list(ingresos_categoria.values())
        egresos_labels = list(egresos_categoria.keys())
        egresos_values = list(egresos_categoria.values())

        fig3, (ax3, ax4) = plt.subplots(1, 2, figsize=(10, 5))

        if sum(ingresos_values) > 0:
            ax3.pie(
                ingresos_values, labels=ingresos_labels, autopct="%1.1f%%", startangle=90,
                colors=plt.cm.Greens(np.linspace(0.4, 0.8, len(ingresos_labels)))
            )
        else:
            ax3.text(0.5, 0.5, "Sin Ingresos", ha="center", va="center", color="gray")
            ax3.axis("off")

        if sum(egresos_values) > 0:
            ax4.pie(
                egresos_values, labels=egresos_labels, autopct="%1.1f%%", startangle=90,
                colors=plt.cm.YlOrBr(np.linspace(0.4, 0.8, len(egresos_labels)))
            )
        else:
            ax4.text(0.5, 0.5, "Sin Egresos", ha="center", va="center", color="gray")
            ax4.axis("off")

        plt.tight_layout()
        buffer3 = io.BytesIO()
        fig3.savefig(buffer3, format="png", dpi=100, transparent=True, bbox_inches="tight")
        plt.close(fig3)
        buffer3.seek(0)
        pie_chart = f"data:image/png;base64,{base64.b64encode(buffer3.getvalue()).decode()}"

        # ==========================
        # ANÁLISIS DE RENDIMIENTO PORCENTUAL
        # ==========================
        ingresos_netos_float = money_to_float(e.total_ingresos)
        egresos_netos_float = money_to_float(e.total_egresos)

        gastos_valores = np.array([money_to_float(g["value"]) for g in raw_gastos], dtype=float)
        ingresos_valores = np.array([money_to_float(g["value"]) for g in raw_ingresos], dtype=float)

        if egresos_netos_float > 0:
            gastos_porcentajes = np.round((gastos_valores / egresos_netos_float) * 100).astype(int)
        else:
            gastos_porcentajes = np.zeros_like(gastos_valores, dtype=int)

        if ingresos_netos_float > 0:
            ingresos_porcentajes = np.round((ingresos_valores / ingresos_netos_float) * 100).astype(int)
        else:
            ingresos_porcentajes = np.zeros_like(ingresos_valores, dtype=int)

        gastos = []
        for g, pct in zip(raw_gastos, gastos_porcentajes):
            gastos.append({
                "title": g["title"],
                "value": money_to_float(g["value"]),
                "porcentaje_gasto": pct,
            })

        ingresos_corrientes = []
        for g, pct in zip(raw_ingresos, ingresos_porcentajes):
            ingresos_corrientes.append({
                "title": g["title"],
                "value": money_to_float(g["value"]),
                "porcentaje_ingresos": pct,
            })

        # ==========================
        # RETORNO DE CONTEXTO INTEGRADO
        # ==========================
        context.update({
            "title": "Resumen Contable",
            "sin_datos": False,
            "table": table_context,
            "header_stats": header_stats,
            "cards": cards,
            "metricas_paap": metricas_paap,
            "gastos": gastos,
            "ingresos_corrientes": ingresos_corrientes,
            "chart_image": bar_chart,
            "scatter_chart_image": scatter_chart,
            "pie_chart_image": pie_chart,
        })
        return context

    def render(self):
        return render_to_string(self.template_name, self.get_context_data())




@register_component
class EstadoKPIsComponentDemo(BaseComponent):
    template_name = "admin/demo/profile_card.html"
    name = "Indicadores Financieros"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):
        e = self.instance
        rows = [
            ["Margen utilidad bruta (%)", e.margen_utilidad_bruta],
            ["Margen utilidad neta (%)", e.margen_utilidad_neta],
            ["Rentabilidad (%)", e.rentabilidad],
            ["Liquidez (%)", e.ratio_cobertura],
        ]
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "KPIs Financieros",
            "table": {"headers": ["Indicador", "Valor"], "rows": rows},
        })
        return context

    def render(self):
        return render_to_string(self.template_name, self.get_context_data())


@register_component
class EstadoAnalisisAvanzadoComponentDemo(BaseComponent):
    template_name = "admin/profile_card.html"
    name = "Análisis Avanzado"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):
        e = self.instance
        activos = e.analisis_flujo_financiero or {}
        rows = [
            ["Punto de equilibrio", e.punto_equilibrio],
            ["Dividendos a accionistas", e.dividendos_accionistas],
            ["Activos totales", activos.get("activos_totales", "—")],
            ["Liquidez sobre activos (%)", activos.get("proporcion_liquidez", "—")],
            ["Egresos sobre activos (%)", activos.get("proporcion_egresos", "—")],
        ]
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Análisis Financiero Avanzado",
            "table": {"headers": ["Métrica", "Resultado"], "rows": rows},
        })
        return context

    def render(self):
        return render_to_string(self.template_name, self.get_context_data())





from .models import EstadoFinanciero


from django.contrib import admin, messages
from django.utils.html import format_html
from unfold.admin import ModelAdmin

# ==========================================
# 1. ACCIÓN PARA EL ADMIN (Listado y Detalle)
# ==========================================
@admin.action(description="🤖 Ejecutar Predicción IA (TimesFM - 6 meses)")
def ejecutar_prediccion_ia_action(modeladmin, request, queryset):
    """
    Acción de administrador para ejecutar el pronóstico de IA 
    en los estados financieros seleccionados.
    """
    exitosos = 0
    errores = 0

    for obj in queryset:
        # Ejecutamos el método que creamos en el modelo
        resultado = obj.ejecutar_y_guardar_prediccion_individual(metrica='utilidad_neta', meses=6)
        
        if resultado.get("success"):
            exitosos += 1
        else:
            errores += 1
            # Opcional: mostrar el error específico del objeto si falla
            messages.error(request, f"Error en ID {obj.id}: {resultado.get('error')}")

    if exitosos > 0:
        messages.success(request, f"Predicción de IA ejecutada con éxito para {exitosos} registro(s).")
    if errores > 0:
        messages.warning(request, f"Hubo {errores} registro(s) que no pudieron procesarse.")

        

@admin.register(EstadoFinanciero)
class EstadoFinancieroAdmin(ModelAdmin):

    # ----------------------------------
    # Componentes visuales
    # ----------------------------------
    list_sections = [
        EstadoResumenContableComponentDemo,
    ]

    actions =[
        duplicar_balances,
        export_to_csv,
        export_to_excel,
        ejecutar_prediccion_ia_action,
    ]

    # ----------------------------------
    # Fieldsets (tabs)
    # ----------------------------------
    fieldsets = (
        ("I. Crear Analítica", {
            "fields": (
                "nombre_banco",
                "total_ingresos_bancos",
                "total_egresos_bancos",
                "fecha_inicio", 
                "fecha_fin", 
            ),
            "classes": ("unfold", "tab-periodo"),
        }),

        ("II. Resumen Contable", {
            "fields": (
                "total_ingresos",
                "total_egresos",
                "utilidad_bruta",
                "utilidad_neta",
            ),
            "classes": ("unfold", "tab-resumen"),
        }),

        ("III. Detalle Egresos", {
            "fields": (
                "gastos_operativos",
                "gastos_nomina",
                "gastos_tributarios",
                "gastos_publicitarios",
                "gastos_legales",
                "declaracion_iva",
                "cuentas_pagar",
                "cuentas_cobrar",
            ),
            "classes": ("unfold", "tab-egresos"),
        }),

        ("IV. Detalle Ingresos", {
            "fields": (
                "ventas",
                "inversiones",
                "deduccion_gastos",
                "acciones_legales",
            ),
            "classes": ("unfold", "tab-ingresos"),
        }),

        ("V. Indicadores Financieros", {
            "fields": (
                "margen_utilidad_bruta",
                "margen_utilidad_neta",
                "rentabilidad",
                "ratio_cobertura",
            ),
            "classes": ("unfold", "tab-kpis"),
        }),

        ("VI. Análisis Avanzado (Flujo)", {
            "fields": (
                "punto_equilibrio",
                "dividendos_accionistas",
                "analisis_flujo_financiero",
            ),
            "classes": ("unfold", "tab-avanzado"),
        }),

        ("VII. Conciliación Bancaria", {
            "fields": (
                "total_efectivo_bancos",
                "total_efectivo",
                "diferencia_ingresos",
                "diferencia_egresos",
                "error_conciliacion_porcentaje",
                "umbral_conciliacion",
                "conciliado",
            ),
            "classes": ("unfold", "tab-conciliacion"),
        }),

        ("VIII. Métricas Financieras y Operativas PaaP", {
            "fields": (
                "arpu",
                "cac",
                "ltv",
                "ratio_ltv_cac",
                "payback_period_meses",
                "churn_rate",
                "nrr",
                "gross_margin_porcentaje",
                "burn_rate",
                "runway_meses",
            ),
            "classes": ("unfold", "tab-paap"),
        }),

        ("IX. Predicciones IA (TimesFM)", {
            "fields": (
                "pred_mes_1",
                "pred_mes_2",
                "pred_mes_3",
                "pred_mes_4",
                "pred_mes_5",
                "pred_mes_6",
                "fecha_ultima_prediccion",
            ),
            "classes": ("unfold", "tab-predicciones"),
        }),
    )

    # ----------------------------------
    # Listado
    # ----------------------------------
    list_display = (
        "fecha_inicio",
        "fecha_fin",
        "total_ingresos",
        "total_egresos",
    )

    list_filter = (
        "fecha_inicio",
        "fecha_fin",
    )

    search_fields = (
        "nombre_banco",
        "fecha_inicio",
        "fecha_fin",
    )

    # ----------------------------------
    # Campos solo lectura
    # ----------------------------------
    readonly_fields = (
        "total_ingresos",
        "total_egresos",
        "utilidad_bruta",
        "utilidad_neta",
        "margen_utilidad_bruta",
        "margen_utilidad_neta",
        "rentabilidad",
        "ratio_cobertura",
        "punto_equilibrio",
        "dividendos_accionistas",
        "analisis_flujo_financiero",
        "acciones_legales",
        "ventas",
        "inversiones",
        "gastos_operativos",
        "gastos_nomina",
        "gastos_tributarios",
        "gastos_publicitarios",
        "gastos_legales",
        "declaracion_iva",
        "deduccion_gastos",
        "cuentas_pagar",
        "cuentas_cobrar",
        "total_efectivo_bancos",
        "total_efectivo",
        "diferencia_ingresos",
        "diferencia_egresos",
        "error_conciliacion_porcentaje",
        "umbral_conciliacion",
        
        # Métricas operativas y PaaP
        "arpu",
        "cac",
        "ltv",
        "ratio_ltv_cac",
        "payback_period_meses",
        "churn_rate",
        "nrr",
        "gross_margin_porcentaje",
        "burn_rate",
        "runway_meses",

        # Predicciones de IA (calculadas por el método torch/TimesFM)
        "pred_mes_1",
        "pred_mes_2",
        "pred_mes_3",
        "pred_mes_4",
        "pred_mes_5",
        "pred_mes_6",
        "fecha_ultima_prediccion",
    )

    unfold_fieldsets = True

    # ----------------------------------
    # Filtro de seguridad por usuario (I+D Core)
    # ----------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(usuario=request.user)

    def save_model(self, request, obj, form, change):
        if not change: 
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            return list(fields) + ["usuario"]
        return fields

    # ------------------------------------------------------------
    # Permisos Nativos Forzados para Staff Activo
    # ------------------------------------------------------------
    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.is_staff and request.user.is_active

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.is_staff and request.user.is_active

    def has_change_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.is_staff and request.user.is_active

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False


    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        
        # Si estamos editando un objeto existente, añadimos un indicador o contexto si es necesario
        obj = self.get_object(request, object_id)
        if obj and obj.usuario:
            extra_context['mostrar_boton_ia'] = True
            
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


from django.template.loader import render_to_string

from django.template.loader import render_to_string
from decimal import Decimal

@register_component
class ActivoPasivoResumenComponentDemo(BaseComponent):
    template_name = "admin/activos_resumen.html"
    name = "Resumen Financiero"

    def __init__(self, request, instance=None):
        self.request = request
        self.instance = instance

    def get_context_data(self, **kwargs):
        obj = self.instance

        if not obj:
            return {}

        def safe(v):
            return float(v) if v else 0.0

        context = super().get_context_data(**kwargs)

        # ===============================
        # ======== ACTIVO ==========
        # ===============================
        if obj.es_activo:

            cards = [
                {
                    "title": "Valor en Libros",
                    "value": safe(obj.net_book_value),
                    "badge": "USD",
                    "badge_color": "primary",
                },
                {
                    "title": "Costo Capitalizado",
                    "value": safe(obj.total_capitalized_cost),
                    "badge": "USD",
                    "badge_color": "success",
                },
                {
                    "title": "Depreciación Acumulada",
                    "value": safe(obj.depreciation_accumulated),
                    "badge": "USD",
                    "badge_color": "warning",
                },
                {
                    "title": "Acciones Equivalentes",
                    "value": safe(obj.shares_equivalent_nominal),
                    "badge": "ACC",
                    "badge_color": "success",
                },
                {
                    "title": "% Capital Social",
                    "value": safe(obj.percentage_of_share_capital),
                    "badge": "%",
                    "badge_color": "primary",
                },
            ]

            context.update({
                "title": "Resumen del Activo",
                "cards": cards,
                "tipo": "activo",
                "extra_data": {
                    "Capital Social": obj.total_share_capital,
                    "Total Acciones": obj.total_shares_issued,
                    "Valor Nominal Acción": obj.nominal_value_per_share,
                }
            })

        # ===============================
        # ======== PASIVO ==========
        # ===============================
        elif obj.es_pasivo:

            cards = [
                {
                    "title": "Saldo Pendiente",
                    "value": safe(obj.saldo_pendiente),
                    "badge": "USD",
                    "badge_color": "primary",
                },
                {
                    "title": "Interés Calculado",
                    "value": safe(obj.interes_calculado),
                    "badge": "USD",
                    "badge_color": "warning",
                },
                {
                    "title": "Total Adeudado",
                    "value": safe(obj.total_adeudado),
                    "badge": "USD",
                    "badge_color": "danger",
                },
                {
                    "title": "Acciones Potenciales",
                    "value": safe(obj.acciones_potenciales),
                    "badge": "ACC",
                    "badge_color": "success",
                },
                {
                    "title": "% Dilución Potencial",
                    "value": safe(obj.porcentaje_dilucion_potencial),
                    "badge": "%",
                    "badge_color": "warning",
                },
            ]

            context.update({
                "title": "Resumen del Pasivo",
                "cards": cards,
                "tipo": "pasivo",
                "extra_data": {
                    "Acreedor": obj.creditor,
                    "Fecha Vencimiento": obj.due_date,
                    "Tasa Interés": obj.interest_rate,
                }
            })

        else:
            return {}

        return context

    def render(self):
        return render_to_string(self.template_name, self.get_context_data())


from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import activos


@admin.register(activos)
class ActivosAdmin(ModelAdmin):

    # =============================
    # COMPONENTE VISUAL
    # =============================
    list_sections = [
        ActivoPasivoResumenComponentDemo,
    ]

    actions =[
    duplicar_balances,
    export_to_csv,
    export_to_excel,
    ]

    # =============================
    # FIELDSETS
    # =============================
    fieldsets = (

        ("I. Tipo de Registro", {
            "fields": (
                "es_activo",
                "es_pasivo",
            ),
        }),

        # -----------------------------
        # ACTIVO
        # -----------------------------
        ("II. Información del Activo", {
            "fields": (
                "asset_code",
                "name",
                "description",
                "category",
                "serial_number",
                "brand",
                "model",
                "status",
            ),
            "classes": ("collapse",),
        }),

        ("III. Finanzas del Activo", {
            "fields": (
                "acquisition_date",
                "acquisition_cost",
                "additional_costs",
                "useful_life_years",
                "residual_value",
                "depreciation_accumulated",
                "book_value",
            ),
            "classes": ("collapse",),
        }),

        ("IV. Información Societaria Activo", {
            "fields": (
                "total_share_capital",
                "total_shares_issued",
                "nominal_value_per_share",
                "book_value_per_share",
                "market_value_per_share",
            ),
            "classes": ("collapse",),
        }),

        # -----------------------------
        # PASIVO
        # -----------------------------
        ("V. Información del Pasivo", {
            "fields": (
                "code",
                "liability_type",
                "origin_date",
                "due_date",
                "initial_amount",
                "payments_made",
                "interest_rate",
                "penalties",
                "financial_expenses",
                "creditor",
                "conversion_price",
            ),
            "classes": ("collapse",),
        }),

        ("VI. Metadatos", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
    )

    unfold_fieldsets = True

    # =============================
    # CAMPOS CONDICIONALES
    # =============================
    conditional_fields = {
        "asset_code": "es_activo",
        "acquisition_cost": "es_activo",
        "code": "es_pasivo",
        "initial_amount": "es_pasivo",
    }

    # =============================
    # LIST DISPLAY
    # =============================
    list_display = (
        "tipo_registro",
        "nombre_display",
        "valor_display",
        "status_display",
    )

    list_filter = (
        "es_activo",
        "es_pasivo",
        "status",
        "liability_type",
    )

    search_fields = (
        "asset_code",
        "code",
        "name",
        "creditor",
    )

    readonly_fields = (
        "book_value",
        "created_at",
        "updated_at",
    )

    # =============================
    # MÉTODOS PARA LISTADO
    # =============================

    def tipo_registro(self, obj):
        if obj.es_activo:
            return "Activo"
        if obj.es_pasivo:
            return "Pasivo"
        return "-"
    tipo_registro.short_description = "Tipo"

    def nombre_display(self, obj):
        return obj.name or obj.asset_code or obj.code
    nombre_display.short_description = "Nombre"

    def valor_display(self, obj):
        if obj.es_activo:
            return obj.net_book_value
        if obj.es_pasivo:
            return obj.total_adeudado
        return "-"
    valor_display.short_description = "Valor"

    def status_display(self, obj):
        return obj.status
    status_display.short_description = "Estado"

# ----------------------------------
    # Filtro de seguridad por usuario (I+D Core)
    # ----------------------------------
    def get_queryset(self, request):
        """
        Filtra el listado para que los usuarios comunes solo vean sus datos,
        mientras que los superusuarios mantienen el control total del holding.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # Suponiendo que tu campo en el modelo se llama 'usuario' o 'owner'
        return qs.filter(usuario=request.user)

    def save_model(self, request, obj, form, change):
        """
        Asigna automáticamente el usuario logueado como propietario 
        del registro al momento de la creación.
        """
        if not change: # Si el registro es nuevo
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        """
        Si agregas el campo 'usuario' a los fieldsets, este método asegura 
        que nadie pueda alterarlo de forma manual, blindando el rastro de auditoría.
        """
        fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            return list(fields) + ["usuario"]
        return fields

# ------------------------------------------------------------
    # Permisos Nativos Forzados para Staff Activo (Gobernanza Automatizada)
    # ------------------------------------------------------------
    def has_view_permission(self, request, obj=None):
        """Permite ver el listado si es staff activo."""
        return request.user.is_authenticated and request.user.is_staff and request.user.is_active

    def has_add_permission(self, request):
        """Permite crear registros si es staff activo."""
        return request.user.is_authenticated and request.user.is_staff and request.user.is_active

    def has_change_permission(self, request, obj=None):
        """Permite editar sus propios registros (get_queryset ya aislará el objeto)."""
        return request.user.is_authenticated and request.user.is_staff and request.user.is_active

    def has_delete_permission(self, request, obj=None):
        """Bloquea el borrado a usuarios comunes si lo deseas, o pon True si pueden borrar lo suyo."""
        if request.user.is_superuser:
            return True
        return False # Por seguridad en el histórico del holding



from typing import Any
from django.contrib import admin
from django.http import HttpRequest
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from .models import SesionCaja, TransaccionCaja


def tabs_callback(request: HttpRequest) -> list[dict[str, Any]]:
    """
    Callback dinámico para generar la navegación por pestañas en django-unfold
    según el contexto de la petición actual.
    """
    return [
        {
            # Identificador de página única para el dashboard o vistas generales
            "page": "caja_dashboard",
            "items": [
                {
                    "title": _("Sesiones de Caja"),
                    "link": reverse_lazy("admin:sba_sesioncaja_changelist"),
                },
                {
                    "title": _("Transacciones Registradas"),
                    "link": reverse_lazy("admin:sba_transaccioncaja_changelist"),
                },
            ],
        },
        {
            # Pestañas asociadas a los modelos transaccionales (vistas de detalle / changeform)
            "models": [
                {"name": "sba.sesioncaja", "detail": True},
                {"name": "sba.transaccioncaja", "detail": True},
            ],
            "items": [
                {
                    "title": _("Resumen de Sesión"),
                    "link": reverse_lazy("admin:sba_sesioncaja_changelist"),
                },
                {
                    "title": _("Transacciones del Turno"),
                    "link": reverse_lazy("admin:sba_transaccioncajachangelist"),
                },
            ],
        },
    ]


@admin.register(SesionCaja)
class SesionCajaAdmin(ModelAdmin):
    list_display = (
        "id",
        "usuario",
        "fecha_apertura",
        "estado",
        "monto_inicial",
        "monto_esperado_cierre",
        "monto_real_cierre",
        "diferencia",
    )
    list_filter = ("estado", "fecha_apertura", "usuario")
    search_fields = ("usuario__username", "usuario__email")
    readonly_fields = (
        "fecha_apertura",
        "monto_esperado_cierre",
        "diferencia",
    )
    autocomplete_fields = ("usuario",)


@admin.register(TransaccionCaja)
class TransaccionCajaAdmin(ModelAdmin):
    list_display = (
        "id",
        "sesion_caja",
        "tipo_transaccion",
        "metodo_pago",
        "monto_neto",
        "codigo_referencia",
        "fecha_transaccion",
    )
    list_filter = ("tipo_transaccion", "metodo_pago", "fecha_transaccion")
    search_fields = ("codigo_referencia", "descripcion", "sesion_caja__id")
    autocomplete_fields = ("sesion_caja",)
    readonly_fields = ("fecha_transaccion",)