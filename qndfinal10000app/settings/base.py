"""
Django settings base configuration.
"""
import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Al modularizar dentro de settings/, subimos 3 niveles al directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-default-key')


# Application definition
INSTALLED_APPS = [
    'sba',
    "unfold",  # before django.contrib.admin
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    "unfold.contrib.location_field",
    "unfold.contrib.constance",

    "import_export",
    "django.contrib.admin",
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
   
    #'sbl',
    #'sbm',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Nombre del proyecto dinámico
PROJECT_NAME = config('PROJECT_NAME')
ROOT_URLCONF = f'{PROJECT_NAME}.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = f'{PROJECT_NAME}.wsgi.application'

# Database Base por defecto (SQLite para pruebas rápidas si no se sobrescribe)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "SmartBusinessAnalytics® - Version Core        ",
    "SITE_SUB_TITLE":"Finanzas & AnalíticaSS",
    "SITE_HEADER": "Finanzas & Analítica", 
    "SITE_SUBHEADER": "by SmartQuail, Inc.",
    "SITE_VERSION": "1.0.0",
    "SITE_DESCRIPTION": "SmartQuail.S.A.S (I+D)",
    "SITE_COPYRIGHT": "Copyright © 2026 SmartQuail S.A.S Todos los derechos reservados.",
    "LOGIN": {  "image": lambda request: static("img/login_sq_bg.png"),
               "password_icon": lambda request: static("icons/eye-solid.svg"),
                "username_icon": lambda request: static("icons/username-icon.svg")
                },
    "LOGOUT": {  "image": lambda request: static("img/login_sq_bg.png"),
                },
    "SITE_DROPDOWN": [
        {
            "icon": "menu_book",
            "title": _("Core® V1.0.1 Realase Notes"),
            "link": reverse_lazy("sba:admin_manual_usuario"),
        },

        {
            "icon": "settings",
            "title": _("Configuración de Usuarios"),
            "link": reverse_lazy("admin:sba_user_changelist"),
        },

    ],
    "SITE_URL": "/",
    "SITE_SYMBOL": "analytics",
    "SITE_LOGO": {"light": lambda request: static("demo/smartbusinessanalytics.png"), "dark": lambda request: static("smartbusinessanalytics.png")},
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "SHOW_UI_WARNINGS": True,
    "ENVIRONMENT": "sba.environment_callback",
    "ENVIRONMENT_TITLE_PREFIX": "sba.environment_title_prefix_callback",
    "DASHBOARD_CALLBACK": "sba.admin.dashboard_callback",
    # Configuración de Tema y Selector Claro / Oscuro
    "THEME": "light",
    "DARK_MODE": True,
    
    
    # Manejo robusto de la foto de perfil del usuario
    "USER_AVATAR": lambda request: (
        request.user.avatar.url 
        if hasattr(request.user, 'avatar') and request.user.avatar and hasattr(request.user.avatar, 'url') 
        else static("demo/images/profile.jpg")
    ),
    
    "USER_DROPDOWN": [
        {
            "title": _("Cambiar contraseña"),
            "icon": "key",
            "link": reverse_lazy("admin:password_change"),
        },
        {
            "title": _("Cerrar sesión"),
            "icon": "logout",
            "link": reverse_lazy("admin:logout"),
        },
    ],
    "LOGIN": {
        "redirect_after": lambda request: reverse_lazy("admin:sba_estadofinanciero_changelist"),
    },
    "BORDER_RADIUS": "7px",
    "COLORS": {
        "base": {
            "50": "oklch(98.5% .002 247.839)",
            "100": "oklch(95% .003 264.542)",
            "200": "oklch(88% .005 264.531)",
            "300": "oklch(75% .008 258.338)",
            "400": "oklch(55% .012 261.325)",
            "500": "oklch(40% .015 264.364)",
            "600": "oklch(30% .018 256.802)",
            "700": "oklch(22% .02 259.733)",
            "800": "oklch(16% .022 256.848)",
            "900": "oklch(11% .025 264.665)",
            "950": "oklch(7% .02 261.692)",
        },
        "primary": {
            "50": "oklch(97% .02 20.0)",
            "100": "oklch(92% .05 20.0)",
            "200": "oklch(84% .10 20.0)",
            "300": "oklch(73% .16 20.0)",
            "400": "oklch(62% .22 25.0)",
            "500": "oklch(53% .25 27.0)",
            "600": "oklch(46% .23 27.0)",
            "700": "oklch(39% .20 27.0)",
            "800": "oklch(33% .17 27.0)",
            "900": "oklch(27% .14 27.0)",
            "950": "oklch(18% .10 27.0)",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-700)",
            "default-dark": "var(--color-base-200)",
            "important-light": "var(--color-base-950)",
            "important-dark": "var(--color-base-50)",
        },
    },
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Análisis & Resultados"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Panel Ejecutivo"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": _("Estados Financieros"),
                        "icon": "account_balance",
                        "link": reverse_lazy("admin:sba_estadofinanciero_changelist"),
                    },
                ],
            },
            {
                "title": _("Gestión Contable"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Ingresos & Egresos"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:sba_movimientofinanciero_changelist"),
                    },
                    {
                        "title": _("Activos & Pasivos"),
                        "icon": "balance",
                        "link": reverse_lazy("admin:sba_activos_changelist"),
                    },
                ],
            },
            {
                "title": _("Operaciones de Caja"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Sesiones Diarias"),
                        "icon": "point_of_sale",
                        "link": reverse_lazy("admin:sba_sesioncaja_changelist"),
                    },
                    {
                        "title": _("Transacciones"),
                        "icon": "receipt",
                        "link": reverse_lazy("admin:sba_transaccioncaja_changelist"),
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": [
                "sba.estadofinanciero",
                "sba.movimientofinanciero",
                "sba.sesioncaja",
                "sba.transaccioncaja",
            ],
            "items": [
                {
                    "title": _("Panel Ejecutivo"),
                    "link": reverse_lazy("admin:index"),
                },
            ],
        },
    ],
}


def dashboard_callback(request, context):
    context.update(
        {
            "modulo": "SmartBusinessAnalytics",
        }
    )
    return context


def environment_callback(request):
    return ["Producción SBA v1.0", "success"]


def badge_callback(request):
    return 0


def permission_callback(request):
    return request.user.has_perm("sba.change_estadofinanciero")


AUTH_USER_MODEL = 'sba.User'