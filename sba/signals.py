from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MovimientoFinanciero,EstadoFinanciero

from .tasks import recalcular_estado_financiero

@receiver(post_save, sender=MovimientoFinanciero)
def trigger_recalculo_estado_financiero(sender, instance, **kwargs):
    """
    Cada vez que se guarda un movimiento, recalcula los estados financieros
    que incluyen la fecha del movimiento usando Celery.
    """
    estados = EstadoFinanciero.objects.filter(
        fecha_inicio__lte=instance.fecha_devengo,
        fecha_fin__gte=instance.fecha_devengo
    )
    for ef in estados:
        # Llamada asíncrona a Celery
        recalcular_estado_financiero.delay(ef.id)
