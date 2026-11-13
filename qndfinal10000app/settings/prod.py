from .base import *

DEBUG = os.environ.get('DEBUG')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=lambda v: [s.strip() for s in v.split(',')])
SITE_ID = 1
domain = os.environ.get('SITE_DOMAIN', 'http://localhost:8000')

CORS_ALLOWED_ORIGINS = [
    f"https://{PROJECT_NAME}.smartquail.io",  # ✅ Correcto
]

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


REDIS_HOST = os.environ.get('REDIS_HOST')  # Cambia esto según tu configuración
REDIS_PORT  = os.environ.get('REDIS_PORT')        # Puerto por defecto de Redis
REDIS_DB  = os.environ.get('REDIS_DB')

EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_HOST_USER_INFO = config("EMAIL_HOST_USER_INFO", default="info@tudominio.com")
EMAIL_HOST_USER_LICENCIAS = config("EMAIL_HOST_USER_LICENCIAS", default="licencias@tudominio.com")
EMAIL_HOST_USER_ACTIVOS = config("EMAIL_HOST_USER_ACTIVOS", default="licencias@tudominio.com")
EMAIL_HOST_USER_CTO = config("EMAIL_HOST_USER_CTO", default="licencias@tudominio.com")


MAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
DEFAULT_FROM_EMAIL_LICENCIAS = EMAIL_HOST_USER_LICENCIAS 
DEFAULT_FROM_EMAIL_INFO = EMAIL_HOST_USER_INFO
DEFAULT_FROM_EMAIL_ACTIVOS  = EMAIL_HOST_USER_ACTIVOS 
DEFAULT_FROM_EMAIL_CTO = EMAIL_HOST_USER_CTO 



# ==========================================
# CONFIGURACIÓN DE BASE DE DATOS (POSTGRESQL)
# ==========================================
DB_USERNAME = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")
DB_DATABASE = os.environ.get("POSTGRES_DB", "smartquail_db")
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_ENGINE = os.environ.get("POSTGRES_ENGINE", "django.db.backends.postgresql")

# Forzar siempre PostgreSQL en producción si las credenciales base existen
DATABASES = {
    'default': {
        'ENGINE': DB_ENGINE,
        'NAME': DB_DATABASE,
        'USER': DB_USERNAME,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}


# Configuración de AWS
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL")  # Ej: https://qnd031-static.s3.amazonaws.com

AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
    "ACL": "public-read"  # Cambia a 'private' si los archivos deben ser privados
}


# Configuración de almacenamiento
# Carpetas de static y media dentro del bucket
AWS_LOCATION = os.environ.get("AWS_LOCATION")  # default = qn041app

# Asegúrate de que la URL de los archivos estáticos esté correcta
STATIC_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_LOCATION}/static/'
MEDIA_URL =  f'{AWS_S3_ENDPOINT_URL}/{AWS_LOCATION}/media/'
DEFAULT_FILE_STORAGE = os.environ.get("MEDIA_STORAGE")
STATICFILES_STORAGE =  os.environ.get("STATICFILES_STORAGE")
