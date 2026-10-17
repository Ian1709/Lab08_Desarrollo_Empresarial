from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from quiz.views import ExamenViewSet, OpcionViewSet, PreguntaViewSet

router = DefaultRouter()
router.register(r'examenes', ExamenViewSet, basename='examen')
router.register(r'preguntas', PreguntaViewSet, basename='pregunta')
router.register(r'opciones', OpcionViewSet, basename='opcion')

urlpatterns = [
    path('admin/', admin.site.urls),
    # Inicio de sesión para la API navegable (sesión + CSRF); los clientes de
    # programación usan token, no esto.
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include(router.urls)),
    # Parte 1 (lab extra): el contrato. Una descripción legible por máquina de
    # cada operación de la API; es lo que leen el cliente y la pasarela del agente.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
