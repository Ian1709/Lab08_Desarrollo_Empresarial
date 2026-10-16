from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from quiz.views import ExamenViewSet, OpcionViewSet, PreguntaViewSet

router = DefaultRouter()
router.register(r'examenes', ExamenViewSet, basename='examen')
router.register(r'preguntas', PreguntaViewSet, basename='pregunta')
router.register(r'opciones', OpcionViewSet, basename='opcion')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
