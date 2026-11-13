from django.apps import AppConfig

class sbaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Debe ser el nombre completo del módulo Python
    name = 'sba'
    verbose_name = 'SmartBusinessAnalytics® (EAP)'

    def ready(self):
        import sba.signals
