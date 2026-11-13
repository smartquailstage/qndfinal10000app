from django.db import models
from djmoney.models.fields import MoneyField
from decimal import Decimal
from django.utils.timezone import now
from django.db.models import Sum
from djmoney.money import Money
from decimal import Decimal
import uuid
import hashlib
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.templatetags.static import static

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.templatetags.static import static

class User(AbstractUser):
    # Campo para almacenar la foto de perfil en media/avatars/
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        verbose_name="Foto de perfil",
        help_text="Sube una imagen de perfil en formato PNG, JPG o WEBP."
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        related_name="sba_user_set",
        related_query_name="sba_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        related_name="sba_user_set",
        related_query_name="sba_user",
    )

    @property
    def avatar_url(self) -> str:
        """Devuelve la URL de la foto subida o el avatar por defecto si no tiene."""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return static("demo/images/avatar.webp")

    @property
    def avatar_badge_variant(self) -> str | None:
        return "primary"

    @property
    def avatar_badge_count(self) -> str | int | None:
        return 0 

    @property
    def avatar_badge_url(self) -> str | None:
        return "https://ec.smartquail.io"


        

class MovimientoFinanciero(models.Model):
    """
    Modelo financiero unificado para Ingresos y Egresos
    """

    # ======================================================
    # IDENTIFICACIÓN
    # ======================================================
    hash_registro = models.CharField(
        max_length=64,
       # unique=True,
        editable=False,
        null=True,
        blank=True,
        help_text="Hash único del movimiento financiero, generado automáticamente para trazabilidad."
    )

    usuario = models.ForeignKey('User', on_delete=models.CASCADE)

    codigo_referencia = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Código de referencia del documento (factura, recibo, comprobante, etc.)."
    )

    fecha_devengo = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha en la que el movimiento se reconoce contablemente."
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        help_text="Fecha y hora en que el movimiento fue registrado en el sistema."
    )

    es_ingreso = models.BooleanField(
        default=True,
        help_text="Indica si el movimiento corresponde a un ingreso (True) o a un egreso (False)."
    )

    es_egreso = models.BooleanField(
        default=False,
        help_text="Indica si el movimiento corresponde a un ingreso (False) o a un egreso (True)."
    )

    # ======================================================
    # CLASIFICACIÓN CONTABLE
    # ======================================================
    CATEGORIA_CHOICES = [
        ("gastos_fijos", "Gastos fijos (servicios)"),
        ("gastos_operativos", "Gastos operativos"),
        ("gastos_publicitarios", "Gastos publicitarios"),
        ("gastos_legales", "Gastos legales"),
        ("gastos_nomina", "Gastos de nómina"),
        ("gastos_tributarios", "Gastos tributarios"),
        ("pago_deuda", "Pago de Deuda"),
       
    ]

    CATEGORIA_INGRESOS_CHOICES = [
        ("ventas", "Ventas"),
        ("deducciones", "Deducción Tributaria"),
        ("inversion", "Inversión"),
        ("acciones_legales", "Acción Legal"),
    ]

    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIA_CHOICES,
        null=True,
        blank=True,
        help_text="Clasificación contable del movimiento financiero."
    )

    categoria_ingresos = models.CharField(
        max_length=30,
        choices=CATEGORIA_INGRESOS_CHOICES,
        null=True,
        blank=True,
        help_text="Clasificación contable del movimiento financiero."
    )

    descripcion = models.TextField(
        null=True,
        blank=True,
        help_text="Descripción detallada del movimiento financiero."
    )

    # ======================================================
    # CONTRAPARTE
    # ======================================================
    contraparte_nombre = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Nombre del cliente, proveedor o entidad relacionada con el movimiento."
    )

    contraparte_identificacion_fiscal = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Identificación fiscal de la contraparte (RFC, NIT, CIF, etc.)."
    )

    # ======================================================
    # MONTOS BASE
    # ======================================================
    monto_bruto = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        help_text="Monto bruto del movimiento antes de descuentos e impuestos."
    )

    descuento = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        help_text="Descuento aplicado al monto bruto."
    )

    tasa_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        null=True,
        blank=True,
        help_text="Tasa de IVA aplicada al movimiento. Ejemplo: 0.16 para 16%."
    )

    # ======================================================
    # RESULTADOS TRIBUTARIOS (AUTO)
    # ======================================================
    base_imponible = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        editable=False,
        help_text="Monto sobre el cual se calcula el IVA."
    )

    iva = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        editable=False,
        help_text="IVA calculado automáticamente."
    )

    monto_neto = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        editable=False,
        help_text="Monto total final del movimiento con impuestos incluidos."
    )

    # ======================================================
    # COSTOS Y UTILIDADES
    # ======================================================
    costo_directo = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        help_text="Costo directo asociado al movimiento."
    )

    gastos_indirectos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        help_text="Gastos indirectos asociados al movimiento."
    )

    utilidad_bruta = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        editable=False,
        help_text="Resultado de restar el costo directo a la base imponible."
    )

    utilidad_neta = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        editable=False,
        help_text="Resultado final después de descontar gastos indirectos."
    )

    # ======================================================
    # ESTADO DEL MOVIMIENTO
    # ======================================================
    confirmado = models.BooleanField(
        default=False,
        help_text="Indica si el movimiento ya fue confirmado/validado contablemente.",
        verbose_name="Acreditado"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
        help_text="Fecha y hora en que el movimiento se creó en el sistema.",
        null=True, blank=True
    )



    # ======================================================
    # MÉTODOS INTERNOS
    # ======================================================
    def generar_hash(self):
        raw = f"{uuid.uuid4()}-{self.codigo_referencia}-{self.fecha_devengo}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def calcular_finanzas(self):
        moneda = self.monto_bruto.currency if self.monto_bruto else "USD"

        bruto = self.monto_bruto or Money(0, moneda)
        descuento = self.descuento or Money(0, moneda)
        costo = self.costo_directo or Money(0, moneda)
        gastos = self.gastos_indirectos or Money(0, moneda)
        tasa = self.tasa_iva or Decimal("0.00")

        self.base_imponible = bruto - descuento
        self.iva = self.base_imponible * tasa
        self.monto_neto = self.base_imponible + self.iva
        self.utilidad_bruta = self.base_imponible - costo
        self.utilidad_neta = self.utilidad_bruta - gastos

    def clean(self):
        """
        Validaciones antes de guardar:
        - Debe ser ingreso o egreso.
        - Solo uno puede ser True.
        - monto_bruto nunca debe ser None.
        """
        if not self.es_ingreso and not self.es_egreso:
            raise ValidationError("El movimiento debe ser ingreso o egreso.")
        if self.es_ingreso and self.es_egreso:
            raise ValidationError("Un movimiento no puede ser ingreso y egreso al mismo tiempo.")

        # Asegurarse que monto_bruto tenga valor
        if self.monto_bruto is None:
            from djmoney.money import Money
            self.monto_bruto = Money(0, 'USD')
        if self.descuento is None:
            from djmoney.money import Money
            self.descuento = Money(0, 'USD')
        if self.costo_directo is None:
            from djmoney.money import Money
            self.costo_directo = Money(0, 'USD')
        if self.gastos_indirectos is None:
            from djmoney.money import Money
            self.gastos_indirectos = Money(0, 'USD')

    def save(self, *args, **kwargs):
        # Validar reglas de negocio antes de guardar
        self.clean()

        # Generar hash si no existe
        if not self.hash_registro:
            self.hash_registro = self.generar_hash()

        # Calcular montos automáticamente
        self.calcular_finanzas()

        super().save(*args, **kwargs)


    # ======================================================
    # METADATA
    # ======================================================
    class Meta:
        app_label = "sba"
        verbose_name = "Movimiento Financiero"
        verbose_name_plural = "Movimientos Financieros"
        ordering = ["-fecha_devengo"]

    def __str__(self):
        tipo = "Ingreso" if self.es_ingreso else "Egreso"
        return f"{tipo} | {self.codigo_referencia or self.hash_registro[:8]}"






class Ingreso(models.Model):
    # ======================================================
    # IDENTIFICACIÓN
    # ======================================================

    usuario = models.ForeignKey('User', on_delete=models.CASCADE)

    codigo_referencia = models.CharField(
        max_length=50,
      #  unique=True,
        verbose_name="Código de referencia",
        help_text="Identificador único del ingreso, como número de factura o recibo."
    )

    descripcion = models.TextField(
        verbose_name="Descripción del ingreso",
        help_text="Detalle del producto o servicio vendido."
    )

    fecha_devengo = models.DateField(
        verbose_name="Fecha de devengo",
        help_text="Fecha en la que el ingreso se reconoce contablemente."
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro",
        help_text="Fecha y hora en que el ingreso se registra en el sistema."
    )

    # ======================================================
    # CLASIFICACIÓN
    # ======================================================
    TIPO_INGRESO_CHOICES = [
        ('producto', 'Venta de producto'),
        ('servicio', 'Prestación de servicio'),
        ('suscripcion', 'Ingreso recurrente'),
        ('otro', 'Otro'),
    ]

    tipo_ingreso = models.CharField(
        max_length=20,
        choices=TIPO_INGRESO_CHOICES,
        verbose_name="Tipo de ingreso",
        help_text="Clasificación contable del ingreso."
    )

    producto_servicio = models.CharField(
        max_length=150,
        verbose_name="Producto o servicio",
        help_text="Producto o servicio que genera el ingreso."
    )

    # ======================================================
    # CLIENTE
    # ======================================================
    cliente_nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre del cliente",
        help_text="Nombre del cliente que realiza el pago."
    )

    cliente_identificacion_fiscal = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Identificación fiscal del cliente",
        help_text="RFC, NIT, CIF u otro identificador fiscal."
    )

    # ======================================================
    # MONTOS BASE
    # ======================================================
    monto_bruto = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Monto bruto",
        help_text="Valor total de la venta antes de descuentos e impuestos."
    )

    descuento = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Descuento",
        help_text="Descuento aplicado a la venta."
    )

    tasa_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.16"),
        verbose_name="Tasa de IVA",
        help_text="Porcentaje de IVA aplicable. Ejemplo: 0.16 para 16%."
    )

    # ======================================================
    # RESULTADOS TRIBUTARIOS (AUTO)
    # ======================================================
    base_imponible = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        editable=False,
        verbose_name="Base imponible",
        help_text="Monto sobre el cual se calcula el IVA (calculado automáticamente)."
    )

    iva = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        editable=False,
        verbose_name="IVA",
        help_text="Impuesto al Valor Agregado calculado automáticamente."
    )

    monto_neto = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        editable=False,
        verbose_name="Monto neto",
        help_text="Monto final del ingreso con impuestos incluidos."
    )

    # ======================================================
    # COSTOS Y UTILIDADES (AUTO)
    # ======================================================
    costo_producto = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Costo del producto",
        help_text="Costo directo del producto o servicio vendido."
    )

    gastos_asociados = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Gastos asociados",
        help_text="Gastos indirectos relacionados con la venta."
    )

    utilidad_bruta = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        editable=False,
        verbose_name="Utilidad bruta",
        help_text="Resultado de restar el costo del producto a la base imponible."
    )

    utilidad_neta = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        editable=False,
        verbose_name="Utilidad neta",
        help_text="Utilidad final luego de descontar costos y gastos asociados."
    )

    # ======================================================
    # COBRO
    # ======================================================
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia bancaria'),
        ('tarjeta', 'Tarjeta'),
        ('pago_electronico', 'Pago electrónico'),
    ]

    BANCOS_CHOICES = [
        ("banco_pichincha", "Banco Pichincha"),
        ("banco_guayaquil", "Banco de Guayaquil"),
        ("produbanco", "Produbanco"),
        ("banco_internacional", "Banco Internacional"),
        ("banco_del_austro", "Banco del Austro"),
        ("banco_provincial", "Banco del Pacífico"),
        ("coopac", "Cooperativa COOPAC"),
        ("banco_bolivariano", "Banco Bolivariano"),
        ("banco_dell_sol", "Banco del Sol"),
        ("banco_machala", "Banco Machala"),
        ("banco_farmacias", "Banco de las Farmacias"),
        ("banco_florencia", "Banco Florencia"),
        ("banco_ambato", "Banco Ambato"),
        ("visa", "Visa"),
        ("mastercard", "Mastercard"),
        ("amex", "American Express"),
        ("diners", "Diners Club"),
        ("discover", "Discover"),
        ("jcb", "JCB"),
        ("unionpay", "UnionPay"),
        ("paymentez", "Paymentez"),
        ("datafast", "Datafast"),
        ("payphone", "PayPhone"),
        ("banco_pichincha_online", "Banco Pichincha Online"),
        ("banco_guayaquil_online", "Banco de Guayaquil Online"),
        ("redeban", "Redeban"),
        ("paypal", "PayPal"),
        ("stripe", "Stripe"),
        ("mercadopago", "MercadoPago"),
        ("square", "Square"),
        ("otros", "Otro"),
    ]

    banco = models.CharField(
        max_length=30,
        choices=BANCOS_CHOICES,
        null=True,
        blank=True,
        verbose_name="Institución Bancaria",
        help_text="Banco donde se realiza el cobro."
    )

    codigo_referencia_pago = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Código de referencia de pago",
        help_text="Número de referencia de la transacción bancaria o comprobante de pago."
    )

    metodo_pago = models.CharField(
        max_length=30,
        choices=METODO_PAGO_CHOICES,
        verbose_name="Método de pago",
        help_text="Forma en la que el cliente realiza el pago."
    )

    fecha_cobro = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de cobro",
        help_text="Fecha en la que se recibió el pago."
    )

    cobrado = models.BooleanField(
        default=False,
        verbose_name="Ingreso cobrado",
        help_text="Indica si el ingreso ya fue cobrado."
    )

    # ======================================================
    # MÉTODO SAVE CORREGIDO
    # ======================================================
    def save(self, *args, **kwargs):
        moneda = self.monto_bruto.currency if self.monto_bruto else 'USD'

        # Valores seguros
        monto_bruto = self.monto_bruto or Money(0, moneda)
        descuento = self.descuento or Money(0, moneda)
        costo = self.costo_producto or Money(0, moneda)
        gastos = self.gastos_asociados or Money(0, moneda)
        tasa = self.tasa_iva or 0

        # Cálculos automáticos
        self.base_imponible = monto_bruto - descuento
        self.iva = self.base_imponible * tasa
        self.monto_neto = self.base_imponible + self.iva
        self.utilidad_bruta = self.base_imponible - costo
        self.utilidad_neta = self.utilidad_bruta - gastos

        super().save(*args, **kwargs)

    # ======================================================
    # METADATA Y STR
    # ======================================================
    class Meta:
        app_label = "sba"
        verbose_name = "Ingreso"
        verbose_name_plural = "Ingresos"
        ordering = ["-fecha_devengo"]

    def __str__(self):
        return f"{self.codigo_referencia} - {self.cliente_nombre}"





from django.db import models
from djmoney.models.fields import MoneyField
from decimal import Decimal


class Egreso(models.Model):
    # ======================================================
    # IDENTIFICACIÓN
    # ======================================================
    codigo_referencia = models.CharField(
        max_length=50,
       # unique=True,
        verbose_name="Código de referencia",
        help_text="Identificador único del egreso, como número de factura o comprobante."
    )

    concepto = models.TextField(
        verbose_name="Concepto del egreso",
        help_text="Detalle del gasto o servicio pagado."
    )

    fecha_devengo = models.DateField(
        verbose_name="Fecha de devengo",
        help_text="Fecha en la que se reconoce contablemente el egreso."
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro",
        help_text="Fecha y hora en que el egreso se registra en el sistema."
    )

    # ======================================================
    # CLASIFICACIÓN
    # ======================================================
    TIPO_EGRESO_CHOICES = [
        ('compra', 'Compra de producto'),
        ('servicio', 'Pago de servicio'),
        ('nomina', 'Nómina y remuneraciones'),
        ('otro', 'Otro'),
    ]

    tipo_egreso = models.CharField(
        max_length=20,
        choices=TIPO_EGRESO_CHOICES,
        verbose_name="Tipo de egreso",
        help_text="Clasificación contable del egreso."
    )

    # ======================================================
    # PROVEEDOR / BENEFICIARIO
    # ======================================================
    proveedor_nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre del proveedor",
        help_text="Nombre de la persona o empresa beneficiaria del pago."
    )

    proveedor_identificacion_fiscal = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Identificación fiscal",
        help_text="RFC, NIT, CIF u otro identificador fiscal del proveedor."
    )

    # ======================================================
    # MONTOS BASE (MoneyField)
    # ======================================================
    monto_bruto = MoneyField(
        max_digits=10,
        default_currency='USD',
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto bruto",
        help_text="Valor total del egreso antes de descuentos e impuestos."
    )

    descuento = MoneyField(
        max_digits=10,
        default_currency='USD',
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Descuento",
        help_text="Descuento aplicado al egreso."
    )

    tasa_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.12"),
        verbose_name="Tasa de IVA",
        help_text="Porcentaje de IVA aplicable. Ejemplo: 0.12 para 12%."
    )

    # ======================================================
    # RESULTADOS TRIBUTARIOS (AUTO)
    # ======================================================
    base_imponible = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        editable=False,
        verbose_name="Base imponible",
        help_text="Monto sobre el cual se calcula el IVA (calculado automáticamente)."
    )

    iva = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        editable=False,
        verbose_name="IVA",
        help_text="Impuesto al Valor Agregado calculado automáticamente."
    )

    monto_neto = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        editable=False,
        verbose_name="Monto neto",
        help_text="Monto final del egreso con impuestos incluidos."
    )

    # ======================================================
    # COSTOS Y UTILIDADES (AUTO)
    # ======================================================
    costo_asociado = MoneyField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default_currency='USD',
        verbose_name="Costo asociado",
        help_text="Costo directo relacionado con el egreso."
    )

    gastos_adicionales = MoneyField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default_currency='USD',
        verbose_name="Gastos adicionales",
        help_text="Gastos indirectos relacionados con el egreso."
    )

    utilidad_bruta = MoneyField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default_currency='USD',
        editable=False,
        verbose_name="Utilidad bruta",
        help_text="Resultado de restar los costos a la base imponible."
    )

    utilidad_neta = MoneyField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        default_currency='USD',
        verbose_name="Utilidad neta",
        help_text="Utilidad final luego de descontar gastos adicionales."
    )

    # ======================================================
    # PAGO
    # ======================================================
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia bancaria'),
        ('tarjeta', 'Tarjeta'),
        ('pago_electronico', 'Pago electrónico'),
    ]

    metodo_pago = models.CharField(
        max_length=30,
        choices=METODO_PAGO_CHOICES,
        verbose_name="Método de pago",
        help_text="Forma en la que se realizó el pago."
    )

    pagado = models.BooleanField(
        default=False,
        verbose_name="Pagado",
        help_text="Indica si el egreso ya fue pagado."
    )

    fecha_pago = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de pago",
        help_text="Fecha en la que se realizó el pago."
    )

    # ======================================================
    # CÁLCULOS AUTOMÁTICOS
    # ======================================================
    def save(self, *args, **kwargs):
        if self.monto_bruto:
            descuento = self.descuento or 0
            self.base_imponible = self.monto_bruto - descuento
            self.iva = self.base_imponible * self.tasa_iva
            self.monto_neto = self.base_imponible + self.iva

            if self.costo_asociado:
                self.utilidad_bruta = self.base_imponible - self.costo_asociado
                gastos = self.gastos_adicionales or 0
                self.utilidad_neta = self.utilidad_bruta - gastos

        super().save(*args, **kwargs)

    class Meta:
        app_label = "sba"
        verbose_name = "Egreso"
        verbose_name_plural = "Egresos"
        ordering = ["-fecha_devengo"]

    def __str__(self):
        return f"{self.codigo_referencia} - {self.proveedor_nombre}"




from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from .models import Ingreso, Egreso
from django.db.models.signals import post_save
from django.dispatch import receiver

from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from decimal import Decimal, ROUND_HALF_UP
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from django.db import models


from django.db import models
from decimal import Decimal
from djmoney.models.fields import MoneyField


from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.money import Money

class EstadoFinanciero(models.Model):

    BANCOS_CHOICES = [
        ("banco_pichincha", "Banco Pichincha"),
        ("Banco Guayaquil", "Banco de Guayaquil"),
        ("produbanco", "Produbanco"),
        ("banco_internacional", "Banco Internacional"),
        ("banco_del_austro", "Banco del Austro"),
        ("banco_provincial", "Banco del Pacífico"),
        ("coopac", "Cooperativa COOPAC"),
        ("banco_bolivariano", "Banco Bolivariano"),
        ("banco_dell_sol", "Banco del Sol"),
        ("banco_machala", "Banco Machala"),
        ("banco_farmacias", "Banco de las Farmacias"),
        ("banco_florencia", "Banco Florencia"),
        ("banco_ambato", "Banco Ambato"),
        ("visa", "Visa"),
        ("mastercard", "Mastercard"),
        ("amex", "American Express"),
        ("diners", "Diners Club"),
        ("discover", "Discover"),
        ("jcb", "JCB"),
        ("unionpay", "UnionPay"),
        ("paymentez", "Paymentez"),
        ("datafast", "Datafast"),
        ("payphone", "PayPhone"),
        ("banco_pichincha_online", "Banco Pichincha Online"),
        ("banco_guayaquil_online", "Banco de Guayaquil Online"),
        ("redeban", "Redeban"),
        ("paypal", "PayPal"),
        ("stripe", "Stripe"),
        ("mercadopago", "MercadoPago"),
        ("square", "Square"),
        ("otros", "Otro"),
    ]

    usuario = models.ForeignKey('User', on_delete=models.CASCADE)
    
    # PERÍODO DE ANÁLISIS
    fecha_inicio = models.DateField(
        verbose_name="Elegir fecha de inicio para análisis",
        help_text="Fecha inicial del período contable analizado"
    )

    fecha_fin = models.DateField(
        verbose_name="Elegir fecha de fin para análisis",
        help_text="Fecha de corte del período contable analizado"
    )

    # MOVIMIENTOS BANCARIOS
    total_ingresos_bancos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        verbose_name="Ingresos bancarios",
        null=True,
        blank=True,
        help_text="Escriba el valor total de ingresos registrados e identificados en las cuentas bancarias, Ej: 1000.2"
    )

    total_egresos_bancos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Egresos bancarios",
        help_text="Escriba el valor total de egresos registrados e identificados en las cuentas bancarias, Ej: 1000.2"
    )

    nombre_banco =  models.CharField(
        max_length=30,
        choices=BANCOS_CHOICES,
        default ="banco_guayaquil",
        null=True,
        blank=True,
        verbose_name="Institución Bancaria",
        help_text="Identifique el banco correspondiente para analizar."
    )

    # RESULTADOS CONTABLES AGREGADOS
    total_efectivo_bancos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Efectivo Bancos",
        help_text="Total efectivo en bancos registrados"
    )

    total_efectivo = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Efectivo Contable",
        help_text="Total de Efectivo contable"
    )

    total_ingresos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Ingresos contables",
        help_text="Total de ingresos registrados en la contabilidad"
    )

    total_egresos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Egresos contables",
        help_text="Total de egresos registrados en la contabilidad"
    )

    utilidad_bruta = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Utilidad bruta",
        help_text="Resultado de ingresos menos costos directos"
    )

    utilidad_neta = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Utilidad neta",
        help_text="Resultado final después de impuestos y gastos"
    )

    # CONCILIACIÓN BANCARIA
    diferencia_ingresos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Diferencia de ingresos",
        help_text="Diferencia absoluta entre ingresos bancarios y contables"
    )

    diferencia_egresos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Diferencia de egresos",
        help_text="Diferencia absoluta entre egresos bancarios y contables"
    )

    error_conciliacion_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Error de conciliación (%)",
        help_text="Porcentaje de error entre ingresos bancarios y contables"
    )

    umbral_conciliacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        verbose_name="Umbral de conciliación (%)",
        help_text="Porcentaje máximo permitido para considerar conciliado"
    )

    conciliado = models.BooleanField(
        default=False,
        verbose_name="Conciliado",
        help_text="Indica si la conciliación bancaria es aceptable"
    )

    # INDICADORES FINANCIEROS Y DE UNIDAD (ESTILO PAAP / SMARTQUAIL)
    margen_utilidad_bruta = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Margen de utilidad bruta (%)",
        help_text="Porcentaje de utilidad bruta sobre los ingresos totales"
    )

    margen_utilidad_neta = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Margen de utilidad neta (%)",
        help_text="Porcentaje de utilidad neta sobre los ingresos totales"
    )

    rentabilidad = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Rentabilidad (%)",
        help_text="Indicador de rendimiento financiero del período"
    )

    ratio_cobertura = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Ratio de cobertura",
        help_text="Capacidad de cubrir obligaciones financieras"
    )

    # NUEVAS MÉTRICAS FINANCIERAS AGREGADAS (LTV, CAC, LTV:CAC, Payback, ARPU, Churn, NRR, Gross Margin, Burn Rate, Runway)
    arpu = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="ARPU",
        help_text="Ingreso promedio por usuario o cuenta corporativa activa"
    )

    cac = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="CAC",
        help_text="Costo de adquisición de clientes"
    )

    ltv = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="LTV",
        help_text="Valor de vida del cliente"
    )

    ratio_ltv_cac = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Ratio LTV:CAC",
        help_text="Eficiencia de capital comercial y adquisición"
    )

    payback_period_meses = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Payback Period (meses)",
        help_text="Periodo de recuperación del CAC en meses"
    )

    churn_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Churn Rate (%)",
        help_text="Tasa de cancelación mensual o del período"
    )

    nrr = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Net Revenue Retention (NRR %)",
        help_text="Retención neta de ingresos de clientes existentes"
    )

    gross_margin_porcentaje = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Gross Margin (%)",
        help_text="Porcentaje de margen bruto de entrega del servicio"
    )

    burn_rate = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Burn Rate",
        help_text="Tasa de quema de caja neta mensual"
    )

    runway_meses = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Runway (meses)",
        help_text="Meses de supervivencia financiera con la caja actual"
    )

    # GASTOS Y APLICACIONES
    ventas = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Ventas",
        help_text="Total de ingresos por ventas"
    )

    porcentaje_ventas = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Porcentaje de ventas (%)",
        help_text="Porcentaje de ventas sobre la utilidad neta"
    )

    inversiones = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Inversiones",
        help_text="Monto destinado a inversiones"
    )

    acciones_legales = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Acciones legales",
        help_text="Gastos asociados a procesos legales"
    )

    gastos_fijos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Gastos fijos",
        help_text="Gastos recurrentes y permanentes"
    )

    gastos_operativos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Gastos operativos",
        help_text="Gastos necesarios para la operación del negocio"
    )

    gastos_publicitarios = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Gastos publicitarios",
        help_text="Inversión en publicidad y marketing"
    )

    gastos_legales = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Gastos legales",
        help_text="Honorarios y costos legales"
    )

    gastos_nomina = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Gastos de nómina",
        help_text="Costos salariales y prestaciones"
    )

    gastos_tributarios = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Gastos tributarios",
        help_text="Impuestos y obligaciones fiscales"
    )

    deudas_pagar = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Deudas por pagar",
        help_text="Obligaciones financieras pendientes"
    )

    declaracion_iva = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Declaración de IVA",
        help_text="Monto correspondiente al impuesto al valor agregado"
    )

    deduccion_gastos = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Deducción de gastos",
        help_text="Gastos deducibles para efectos fiscales"
    )

    cuentas_pagar = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Cuentas por pagar",
        help_text="Obligaciones pendientes con proveedores"
    )

    cuentas_cobrar = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Cuentas por cobrar",
        help_text="Montos pendientes de cobro a clientes"
    )

    # CAMPOS AVANZADOS
    punto_equilibrio = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Punto de equilibrio",
        help_text="Nivel de ingresos donde no hay pérdidas ni ganancias"
    )

    dividendos_accionistas = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Dividendos a accionistas",
        help_text="Monto distribuido a los accionistas"
    )

    analisis_flujo_financiero = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Análisis de flujo financiero",
        help_text="Información detallada del flujo de caja en formato estructurado"
    )

    # CAMPOS DE PREDICCIÓN INDIVIDUALIZADA (TIMESFM - 6 MESES ADELANTE)
    pred_mes_1 = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Predicción Mes +1",
        help_text="Valor pronosticado por IA (TimesFM) para el primer mes siguiente al período de análisis."
    )

    pred_mes_2 = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Predicción Mes +2",
        help_text="Valor pronosticado por IA (TimesFM) para el segundo mes hacia adelante."
    )

    pred_mes_3 = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Predicción Mes +3",
        help_text="Valor pronosticado por IA (TimesFM) para el tercer mes hacia adelante."
    )

    pred_mes_4 = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Predicción Mes +4",
        help_text="Valor pronosticado por IA (TimesFM) para el cuarto mes hacia adelante."
    )

    pred_mes_5 = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Predicción Mes +5",
        help_text="Valor pronosticado por IA (TimesFM) para el quinto mes hacia adelante."
    )

    pred_mes_6 = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency='USD',
        null=True,
        blank=True,
        verbose_name="Predicción Mes +6",
        help_text="Valor pronosticado por IA (TimesFM) para el sexto mes hacia adelante (cierre del horizonte trimestral/semestral)."
    )

    fecha_ultima_prediccion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de última predicción",
        help_text="Marca temporal exacta de cuándo se ejecutó por última vez el modelo de series temporales."
    )

    # ==============================
    # MÉTODO PRINCIPAL
    # ==============================
    def calcular_estado_financiero(self, tasa_dividendo=Decimal('0.50'), caja_disponible_total=Decimal('340000.00'), churn_default=Decimal('0.08'), cac_default=Decimal('3500.00')):
        if not self.fecha_inicio or not self.fecha_fin:
            return

        from sba.models import MovimientoFinanciero

        ingresos = MovimientoFinanciero.objects.filter(
            fecha_devengo__range=(self.fecha_inicio, self.fecha_fin),
            es_ingreso=True
        )

        egresos = MovimientoFinanciero.objects.filter(
            fecha_devengo__range=(self.fecha_inicio, self.fecha_fin),
            es_egreso=True
        )

        # ------------------------------
        # Helpers
        # ------------------------------
        def sumar_money(qs, campo):
            total = Money(0, 'USD')
            for obj in qs:
                val = getattr(obj, campo, None)
                if isinstance(val, Money):
                    total += val
            return total

        def d(value):
            return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if value else Decimal('0.00')

        def sumar_por_categoria(qs, categoria, campo='monto_neto'):
            total = Money(0, 'USD')
            for obj in qs.filter(categoria=categoria):
                val = getattr(obj, campo, None)
                if isinstance(val, Money):
                    total += val
            return total

        def sumar_por_categoria_ingresos(qs, categoria_ingresos, campo='monto_neto'):
            total = Money(0, 'USD')
            for obj in qs.filter(categoria_ingresos=categoria_ingresos):
                val = getattr(obj, campo, None)
                if isinstance(val, Money):
                    total += val
            return total

        def sumar_iva_duduccion(qs):
            total = Money(0, 'USD')
            for obj in qs.filter(es_egreso=True):
                if obj.iva:
                    total += obj.iva
            return total

        def sumar_iva_declaracion(qs):
            total = Money(0, 'USD')
            for obj in qs.filter(es_ingreso=True):
                if obj.iva:
                    total += obj.iva
            return total

        def sumar_cuentas_pagar(qs):
            total = Money(0, 'USD')
            for obj in qs.filter(es_egreso=True, confirmado=False):
                if obj.monto_neto:
                    total += obj.monto_neto
            return total

        def sumar_cuentas_cobrar(qs):
            total = Money(0, 'USD')
            for obj in qs.filter(es_ingreso=True, confirmado=False):
                if obj.monto_neto:
                    total += obj.monto_neto
            return total

        def sumar_deudas_pagar(qs):
            total = Money(0, 'USD')
            for obj in qs.filter(es_egreso=True, categoria='pago_deuda'):
                if obj.monto_neto:
                    total += obj.monto_neto
            return total

        def sumar_acciones_legales_pagar(qs):
            total = Money(0, 'USD')
            for obj in qs.filter(es_ingreso=True, categoria_ingresos='acciones_legales'):
                if obj.monto_neto:
                    total += obj.monto_neto
            return total

        def ratio(num, den):
            if den <= 0:
                return Decimal('0.00')
            return (num / den * Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # ------------------------------
        # GASTOS y VENTAS primero
        # ------------------------------
        self.ventas = sumar_por_categoria_ingresos(ingresos, 'ventas')
        self.inversiones = sumar_por_categoria_ingresos(ingresos, 'inversion')
        self.acciones_legales = sumar_acciones_legales_pagar(ingresos)
        self.gastos_operativos = sumar_por_categoria(egresos, 'gastos_operativos')
        self.gastos_nomina = sumar_por_categoria(egresos, 'gastos_nomina')
        self.gastos_tributarios = sumar_por_categoria(egresos, 'gastos_tributarios')
        self.gastos_publicitarios = sumar_por_categoria(egresos, 'gastos_publicitarios')
        self.gastos_legales = sumar_por_categoria(egresos, 'gastos_legales')
        self.declaracion_iva = sumar_iva_declaracion(ingresos)
        self.deduccion_gastos = sumar_iva_duduccion(egresos)
        self.cuentas_pagar = sumar_cuentas_pagar(egresos)
        self.deudas_pagar = sumar_deudas_pagar(egresos)
        self.cuentas_cobrar = sumar_cuentas_cobrar(ingresos)

        # ------------------------------
        # Totales
        # ------------------------------
        self.total_ingresos = sumar_money(ingresos, 'monto_neto')
        self.total_egresos = sumar_money(egresos, 'monto_neto')
        self.utilidad_bruta = sumar_money(ingresos, 'utilidad_bruta') - sumar_money(egresos, 'costo_directo')
        self.utilidad_neta = sumar_money(ingresos, 'utilidad_neta')

        ingresos_v = d(self.total_ingresos.amount)
        egresos_v = d(self.total_egresos.amount)
        utilidad_neta_v = d(self.utilidad_neta.amount)
        ventas_v = d(self.ventas.amount) if self.ventas else Decimal('0')

        # ------------------------------
        # Porcentaje Ventas / Utilidad Neta
        # ------------------------------
        self.porcentaje_ventas = ratio(ventas_v, utilidad_neta_v).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

        # ------------------------------
        # Indicadores Financieros Base
        # ------------------------------
        self.margen_utilidad_bruta = ratio(d(self.utilidad_bruta.amount), ingresos_v)
        self.margen_utilidad_neta = ratio(utilidad_neta_v, ingresos_v)
        self.rentabilidad = ratio(utilidad_neta_v, ingresos_v)
        self.ratio_cobertura = ratio(ingresos_v, egresos_v)

        # ------------------------------
        # Métricas de Unidad y PaaP Automáticas (ARPU, LTV, CAC, Payback, Churn, NRR, Gross Margin, Burn Rate, Runway)
        # ------------------------------
        num_clientes_estimado = max(1, ingresos.count())
        arpu_val = (ingresos_v / Decimal(num_clientes_estimado)).quantize(Decimal('0.01')) if num_clientes_estimado > 0 else Decimal('0.00')
        self.arpu = Money(arpu_val, 'USD')

        gm_val = self.margen_utilidad_bruta
        self.gross_margin_porcentaje = gm_val

        self.churn_rate = churn_default

        gm_decimal = gm_val / Decimal('100')
        churn_dec = self.churn_rate
        if churn_dec > 0:
            ltv_val = ((arpu_val * gm_decimal) / churn_dec).quantize(Decimal('0.01'))
        else:
            ltv_val = Decimal('0.00')
        self.ltv = Money(ltv_val, 'USD')

        self.cac = Money(cac_default, 'USD')
        cac_val = d(self.cac.amount)

        if cac_val > 0:
            self.ratio_ltv_cac = (ltv_val / cac_val).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            self.ratio_ltv_cac = Decimal('0.00')

        den_payback = arpu_val * gm_decimal
        if den_payback > 0:
            self.payback_period_meses = (cac_val / den_payback).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            self.payback_period_meses = Decimal('0.00')

        self.nrr = Decimal('110.00')
        self.burn_rate = Money(egresos_v, 'USD')

        if egresos_v > 0:
            self.runway_meses = (caja_disponible_total / egresos_v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            self.runway_meses = Decimal('99.99')

        # ------------------------------
        # Punto de equilibrio
        # ------------------------------
        margen_contribucion = ingresos_v - d(sumar_money(egresos, 'costo_directo').amount)
        self.punto_equilibrio = Money(
            (d(sumar_money(egresos, 'monto_neto').amount) / margen_contribucion * ingresos_v).quantize(Decimal('0.01'))
            if margen_contribucion > 0 else 0,
            'USD'
        )

        # ------------------------------
        # Dividendos
        # ------------------------------
        self.dividendos_accionistas = Money(
            (utilidad_neta_v * tasa_dividendo).quantize(Decimal('0.01')) if utilidad_neta_v > 0 else 0,
            'USD'
        )

        # ------------------------------
        # Flujo financiero
        # ------------------------------
        flujo_total = ingresos_v + egresos_v
        self.analisis_flujo_financiero = {
            "ingresos": float(ingresos_v),
            "egresos": float(egresos_v),
            "utilidad_neta": float(utilidad_neta_v),
            "ingresos_pct": float(ratio(ingresos_v, flujo_total)),
            "egresos_pct": float(ratio(egresos_v, flujo_total)),
            "ltv_cac_ratio": float(self.ratio_ltv_cac),
            "payback_meses": float(self.payback_period_meses),
            "runway_meses": float(self.runway_meses),
        }

        # ------------------------------
        # CONCILIACIÓN BANCARIA
        # ------------------------------
        self.total_efectivo = Money(
            (ingresos_v - egresos_v).quantize(Decimal('0.01')),
            'USD'
        )

        bancos_ing = d(self.total_ingresos_bancos.amount) if self.total_ingresos_bancos else Decimal('0')
        bancos_egr = d(self.total_egresos_bancos.amount) if self.total_egresos_bancos else Decimal('0')

        self.total_efectivo_bancos = Money(
            (bancos_ing - bancos_egr).quantize(Decimal('0.01')),
            'USD'
        )

        diferencia = abs(bancos_ing - ingresos_v)
        self.diferencia_ingresos = Money(
            diferencia.quantize(Decimal('0.01')),
            'USD'
        )

        diferencia_egresos = abs(bancos_egr - egresos_v)
        self.diferencia_egresos = Money(
            diferencia_egresos.quantize(Decimal('0.01')),
            'USD'
        )

        if ingresos_v > 0:
            self.error_conciliacion_porcentaje = (
                (diferencia / ingresos_v) * Decimal('100')
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            self.error_conciliacion_porcentaje = Decimal('0.00')

        umbral = (
            self.umbral_conciliacion
            if self.umbral_conciliacion is not None
            else Decimal('1.00')
        )

        self.conciliado = (
            self.error_conciliacion_porcentaje <= umbral
        )



    # ==============================
    # Meta y Métodos
    # ==============================
    class Meta:
        app_label = "sba"
        ordering = ["-fecha_inicio"]
        verbose_name = "Estado de Resultados"
        verbose_name_plural = "Estados de Resultados"

    def save(self, *args, **kwargs):
        recalcular = kwargs.pop("recalcular", True)
        if recalcular and self.fecha_inicio and self.fecha_fin:
            self.calcular_estado_financiero()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Estado Financiero {self.fecha_inicio} - {self.fecha_fin}"

from django.db import models
from decimal import Decimal


class activos(models.Model):

    usuario = models.ForeignKey('User', on_delete=models.CASCADE)


    es_activo = models.BooleanField(default=True,
        help_text="Indica si el movimiento corresponde a un activo")
    # =========================
    # 1. IDENTIFICACIÓN
    # =========================
    asset_code = models.CharField(
        max_length=50,
        # unique=True,
        null=True,
        blank=True,
        verbose_name="Código del activo",
        help_text="Identificador único interno del activo."
    )

    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Nombre del activo",
        help_text="Nombre descriptivo del activo."
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción detallada del activo."
    )

    category = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Categoría",
        help_text="Clasificación del activo (maquinaria, equipo, vehículo, etc.)."
    )

    serial_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Número de serie",
        help_text="Número de serie proporcionado por el fabricante."
    )

    brand = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Marca",
        help_text="Marca comercial del activo."
    )

    model = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Modelo",
        help_text="Modelo específico del activo."
    )

    # =========================
    # 2. INFORMACIÓN FINANCIERA
    # =========================
    acquisition_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de adquisición",
        help_text="Fecha en que el activo fue adquirido."
    )

    acquisition_cost = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Costo de adquisición",
        help_text="Costo inicial pagado por el activo."
    )

    additional_costs = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Costos adicionales",
        help_text="Costos adicionales capitalizables (transporte, instalación, impuestos no recuperables)."
    )

    useful_life_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Vida útil (años)",
        help_text="Número estimado de años de vida útil del activo."
    )

    residual_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor residual",
        help_text="Valor estimado del activo al final de su vida útil."
    )

    depreciation_accumulated = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Depreciación acumulada",
        help_text="Monto total depreciado hasta la fecha."
    )

    book_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor en libros",
        help_text="Valor contable actual del activo (costo menos depreciación)."
    )

    # =========================
    # 3. VALORACIÓN
    # =========================
    fair_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor razonable",
        help_text="Valor determinado mediante avalúo técnico independiente."
    )

    market_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor de mercado",
        help_text="Valor estimado del activo según condiciones actuales del mercado."
    )

    valuation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de valoración",
        help_text="Fecha en que se realizó la última valoración del activo."
    )

    # =========================
    # 4. DATOS SOCIETARIOS
    # =========================
    total_share_capital = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Capital social total",
        help_text="Monto total del capital social suscrito de la empresa."
    )

    total_shares_issued = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Total de acciones emitidas",
        help_text="Número total de acciones emitidas por la sociedad."
    )

    nominal_value_per_share = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor nominal por acción",
        help_text="Valor nominal asignado a cada acción."
    )

    book_value_per_share = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor contable por acción",
        help_text="Valor contable actual de cada acción."
    )

    market_value_per_share = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor de mercado por acción",
        help_text="Precio de mercado actual de cada acción."
    )

    # =========================
    # 5. ESTADO
    # =========================
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('maintenance', 'En mantenimiento'),
        ('disposed', 'Dado de baja'),
        ('sold', 'Vendido'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        null=True,
        blank=True,
        verbose_name="Estado",
        help_text="Estado actual del activo dentro de la empresa."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        verbose_name="Fecha de creación",
        help_text="Fecha en que el registro fue creado en el sistema."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        verbose_name="Fecha de actualización",
        help_text="Fecha de la última actualización del registro."
    )




    # ==============================
    # 1.Pasivos
    # ==============================

    es_pasivo = models.BooleanField(default=True,
        help_text="Indica si el movimiento corresponde a un activo")
    code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        # unique=True,
        verbose_name="Código del pasivo",
        help_text="Identificador único interno del pasivo."
    )

    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Nombre del pasivo",
        help_text="Nombre descriptivo del pasivo."
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Descripción",
        help_text="Detalle o explicación adicional del pasivo."
    )

    LIABILITY_TYPES = [
        ('current', 'Corriente'),
        ('non_current', 'No corriente'),
        ('financial', 'Financiero'),
        ('tax', 'Fiscal'),
        ('labor', 'Laboral'),
        ('commercial', 'Comercial'),
        ('contingent', 'Contingente'),
        ('convertible', 'Convertible'),
    ]

    liability_type = models.CharField(
        max_length=20,
        choices=LIABILITY_TYPES,
        null=True,
        blank=True,
        verbose_name="Tipo de pasivo",
        help_text="Clasificación contable del pasivo."
    )

    # ==============================
    # 2. INFORMACIÓN FINANCIERA
    # ==============================

    origin_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de origen",
        help_text="Fecha en que se generó la obligación."
    )

    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de vencimiento",
        help_text="Fecha límite para cumplir la obligación."
    )

    initial_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto inicial",
        help_text="Monto original de la obligación."
    )

    currency = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name="Moneda",
        help_text="Moneda en la que está expresado el pasivo."
    )

    exchange_rate = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Tipo de cambio",
        help_text="Tipo de cambio aplicado si la moneda es extranjera."
    )

    payments_made = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Pagos realizados",
        help_text="Monto total pagado hasta la fecha."
    )

    interest_rate = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Tasa de interés",
        help_text="Tasa de interés nominal anual expresada en porcentaje."
    )

    interest_accrued_manual = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Intereses acumulados manuales",
        help_text="Intereses acumulados registrados manualmente (si aplica)."
    )

    penalties = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Penalidades",
        help_text="Multas o penalidades acumuladas."
    )

    financial_expenses = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Gastos financieros",
        help_text="Costos financieros adicionales asociados."
    )

    # ==============================
    # 3. INFORMACIÓN CONTRACTUAL
    # ==============================

    creditor = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Acreedor",
        help_text="Entidad o persona a quien se le debe la obligación."
    )

    contract_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Número de contrato",
        help_text="Número identificador del contrato asociado."
    )

    guarantee_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor de la garantía",
        help_text="Valor estimado de la garantía asociada al pasivo."
    )

    # ==============================
    # 4. CONVERTIBLE A ACCIONES
    # ==============================

    conversion_price = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Precio de conversión",
        help_text="Precio por acción en caso de conversión a capital."
    )

    total_shares_issued = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Total de acciones emitidas",
        help_text="Total de acciones actualmente emitidas por la sociedad."
    )

    total_share_capital = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Capital social total",
        help_text="Capital social actual de la empresa."
    )

    # ==============================
    # 5. ESTADO
    # ==============================

    STATUS_CHOICES = [
        ('active', 'Vigente'),
        ('paid', 'Pagado'),
        ('refinanced', 'Refinanciado'),
        ('default', 'En mora'),
        ('cancelled', 'Cancelado'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        null=True,
        blank=True,
        verbose_name="Estado",
        help_text="Estado actual del pasivo."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        verbose_name="Fecha de creación",
        help_text="Fecha de registro en el sistema."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        verbose_name="Fecha de actualización",
        help_text="Última fecha de modificación del registro."

    
    )



    # ==========================================================
    # ================= PROPIEDADES DE CÁLCULO ==================
    # ==========================================================

    @property
    def saldo_pendiente(self):
        if self.initial_amount:
            pagos = self.payments_made or Decimal(0)
            return self.initial_amount - pagos
        return None

    @property
    def interes_calculado(self):
        if self.saldo_pendiente and self.interest_rate and self.origin_date:
            dias = (timezone.now().date() - self.origin_date).days
            tasa_decimal = self.interest_rate / Decimal(100)
            return self.saldo_pendiente * tasa_decimal * Decimal(dias) / Decimal(365)
        return self.interest_accrued_manual

    @property
    def total_adeudado(self):
        saldo = self.saldo_pendiente or Decimal(0)
        interes = self.interes_calculado or Decimal(0)
        penal = self.penalties or Decimal(0)
        gastos = self.financial_expenses or Decimal(0)
        return saldo + interes + penal + gastos

    @property
    def acciones_potenciales(self):
        if self.conversion_price and self.total_adeudado:
            if self.conversion_price > 0:
                return self.total_adeudado / self.conversion_price
        return None

    @property
    def porcentaje_dilucion_potencial(self):
        if self.acciones_potenciales and self.total_shares_issued:
            if self.total_shares_issued > 0:
                return (self.acciones_potenciales / self.total_shares_issued) * 100
        return None

    @property
    def porcentaje_sobre_capital(self):
        if self.total_adeudado and self.total_share_capital:
            if self.total_share_capital > 0:
                return (self.total_adeudado / self.total_share_capital) * 100
        return None

    def __str__(self):
        return f"{self.code or ''} - {self.name or ''}"


    # =====================================================
    # PROPIEDADES DE CÁLCULO
    # =====================================================

    @property
    def total_capitalized_cost(self):
        if self.acquisition_cost and self.additional_costs:
            return self.acquisition_cost + self.additional_costs
        return self.acquisition_cost or Decimal(0)

    @property
    def net_book_value(self):
        if self.total_capitalized_cost and self.depreciation_accumulated:
            return self.total_capitalized_cost - self.depreciation_accumulated
        return self.total_capitalized_cost or Decimal(0)

    @property
    def shares_equivalent_nominal(self):
        if self.nominal_value_per_share and self.net_book_value:
            if self.nominal_value_per_share > 0:
                return self.net_book_value / self.nominal_value_per_share
        return None

    @property
    def shares_equivalent_book(self):
        if self.book_value_per_share and self.net_book_value:
            if self.book_value_per_share > 0:
                return self.net_book_value / self.book_value_per_share
        return None

    @property
    def shares_equivalent_market(self):
        if self.market_value and self.market_value_per_share:
            if self.market_value_per_share > 0:
                return self.market_value / self.market_value_per_share
        return None

    @property
    def percentage_of_share_capital(self):
        if self.total_share_capital and self.net_book_value:
            if self.total_share_capital > 0:
                return (self.net_book_value / self.total_share_capital) * 100
        return None

    @property
    def percentage_of_total_shares(self):
        if self.total_shares_issued and self.shares_equivalent_nominal:
            if self.total_shares_issued > 0:
                return (self.shares_equivalent_nominal / self.total_shares_issued) * 100
        return None

    class Meta:
        app_label = "sba"
        verbose_name = "Movimiento Patrimonial"
        verbose_name_plural = "Movimientos Patrimoniales"
        ordering = ["-updated_at"]

    def save(self, *args, **kwargs):
        self.book_value = self.net_book_value
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset_code or ''} - {self.name or ''}"




from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.money import Money

class SesionCaja(models.Model):
    """
    Representa el turno o apertura de una caja registradora física o digital.
    Controla el efectivo inicial, las entradas/salidas y el arqueo de cierre.
    """
    
    ESTADO_CHOICES = [
        ("abierta", "Abierta (Turno Activo)"),
        ("cerrada", "Cerrada (Arqueado)"),
    ]

    usuario = models.ForeignKey('User', on_delete=models.CASCADE)

    fecha_apertura = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora de Apertura"
    )

    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha y Hora de Cierre"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="abierta",
        verbose_name="Estado de la Caja"
    )

    # Fondos iniciales y finales
    monto_inicial = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        verbose_name="Efectivo Inicial (Fondo de Caja)",
        help_text="Dinero con el que se abre la caja para dar cambio."
    )

    monto_esperado_cierre = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        default=Decimal("0.00"),
        editable=False,
        verbose_name="Monto Esperado en Caja",
        help_text="Calculado automáticamente: Inicial + Ingresos Efectivo - Retiros/Egresos Efectivo."
    )

    monto_real_cierre = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        verbose_name="Efectivo Real Contado",
        help_text="Dinero físico contado al momento del cierre de caja."
    )

    diferencia = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        default=Decimal("0.00"),
        editable=False,
        verbose_name="Diferencia (Sobrante / Faltante)",
        help_text="Diferencia entre el efectivo real contado y el esperado."
    )

    observaciones = models.TextField(
        null=True,
        blank=True,
        verbose_name="Notas de Cierre / Incidencias"
    )

    def calcular_arqueo(self):
        """Calcula el total esperado en caja y la diferencia frente al conteo físico."""
        moneda = self.monto_inicial.currency if self.monto_inicial else "USD"
        
        transacciones = self.transacciones.all()
        
        # Sumamos ingresos en efectivo y restamos egresos/retiros en efectivo
        ingresos_efectivo = sum(
            (t.monto_neto.amount for t in transacciones if t.tipo_transaccion == "venta" and t.metodo_pago == "efectivo" and t.monto_neto),
            Decimal("0.00")
        )
        retiros_efectivo = sum(
            (t.monto_neto.amount for t in transacciones if t.tipo_transaccion == "retiro" and t.monto_neto),
            Decimal("0.00")
        )

        inicial = self.monto_inicial.amount if self.monto_inicial else Decimal("0.00")
        
        esperado = inicial + ingresos_efectivo - retiros_efectivo
        self.monto_esperado_cierre = Money(esperado, moneda)

        if self.monto_real_cierre is not None:
            real = self.monto_real_cierre.amount
            self.diferencia = Money(real - esperado, moneda)

    def save(self, *args, **kwargs):
        if self.pk:
            self.calcular_arqueo()
        super().save(*args, **kwargs)

    class Meta:
        app_label = "sba"
        verbose_name = "Sesión de Caja"
        verbose_name_plural = "Sesiones de Caja"
        ordering = ["-fecha_apertura"]

    def __str__(self):
        return f"Caja #{self.pk} - {self.usuario} [{self.get_estado_display()}]"


class TransaccionCaja(models.Model):
    """
    Representa cada operación transaccional ocurrida dentro de una sesión de caja 
    (ventas, cobros, ingresos manuales de efectivo o retiros/gastos menores).
    """

    TIPO_TRANSACCION_CHOICES = [
        ("venta", "Venta / Cobro"),
        ("ingreso_manual", "Ingreso de Efectivo (Cambio/Fondo)"),
        ("retiro", "Retiro de Efectivo / Gasto Menor"),
    ]

    METODO_PAGO_CHOICES = [
        ("efectivo", "Efectivo"),
        ("tarjeta_credito", "Tarjeta de Crédito"),
        ("tarjeta_debito", "Tarjeta de Débito"),
        ("transferencia", "Transferencia Bancaria"),
    ]

    sesion_caja = models.ForeignKey(
        SesionCaja,
        on_delete=models.PROTECT,
        related_name="transacciones",
        verbose_name="Sesión de Caja"
    )

    tipo_transaccion = models.CharField(
        max_length=30,
        choices=TIPO_TRANSACCION_CHOICES,
        default="venta",
        verbose_name="Tipo de Operación"
    )

    metodo_pago = models.CharField(
        max_length=30,
        choices=METODO_PAGO_CHOICES,
        default="efectivo",
        verbose_name="Método de Pago"
    )

    codigo_referencia = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="N° de Ticket / Factura / Voucher"
    )

    monto_bruto = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        verbose_name="Monto Bruto"
    )

    monto_neto = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        verbose_name="Monto Neto Total"
    )

    cambio_entregado = MoneyField(
        max_digits=12,
        decimal_places=2,
        default_currency="USD",
        default=Decimal("0.00"),
        verbose_name="Cambio / Vuelto Entregado",
        help_text="Efectivo devuelto al cliente si pagó con un monto mayor."
    )

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Concepto o Detalle"
    )

    fecha_transaccion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora"
    )

    def clean(self):
        if self.sesion_caja and self.sesion_caja.estado == "cerrada":
            raise ValidationError("No se pueden registrar transacciones en una sesión de caja cerrada.")

    def save(self, *args, **kwargs):
        self.clean()
        if not self.monto_neto and self.monto_bruto:
            self.monto_neto = self.monto_bruto
        super().save(*args, **kwargs)
        # Actualizar arqueo de la sesión asociada
        self.sesion_caja.save()

    class Meta:
        app_label = "sba"
        verbose_name = "Transacción de Caja"
        verbose_name_plural = "Transacciones de Caja"
        ordering = ["-fecha_transaccion"]

    def __str__(self):
        return f"[{self.get_tipo_transaccion_display()}] {self.monto_neto} ({self.get_metodo_pago_display()})"