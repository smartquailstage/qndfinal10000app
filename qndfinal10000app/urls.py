from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from sba.views import manual_usuario_view

urlpatterns = [
    path('sba/', include('sba.urls')),  # Primero las rutas de la app
    path('', admin.site.urls),          # Después el admin por defecto
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)