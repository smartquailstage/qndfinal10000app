from celery import shared_task
from .models import MovimientoFinanciero,EstadoFinanciero


import logging
logger = logging.getLogger(__name__)

@shared_task
def recalcular_estado_financiero(estado_id):
    try:
        logger.info(f"Recalculando EstadoFinanciero {estado_id}")
        ef = EstadoFinanciero.objects.get(id=estado_id)
        ef.calcular_estado_financiero()
        return f"EstadoFinanciero {estado_id} recalculado."
    except Exception as e:
        logger.error(f"Error recalculando {estado_id}: {e}", exc_info=True)
        raise
