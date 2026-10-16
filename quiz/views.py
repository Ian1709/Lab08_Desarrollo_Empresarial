from rest_framework import viewsets

from .models import Examen, Opcion, Pregunta
from .serializers import (
    ExamenSerializer,
    OpcionSerializer,
    PreguntaSerializer,
)


class ExamenViewSet(viewsets.ModelViewSet):
    """CRUD de exámenes: /api/examenes/"""

    queryset = Examen.objects.all()
    serializer_class = ExamenSerializer


class PreguntaViewSet(viewsets.ModelViewSet):
    """CRUD de preguntas: /api/preguntas/"""

    queryset = Pregunta.objects.select_related('examen').prefetch_related('opciones')
    serializer_class = PreguntaSerializer


class OpcionViewSet(viewsets.ModelViewSet):
    """CRUD de opciones: /api/opciones/"""

    queryset = Opcion.objects.select_related('pregunta')
    serializer_class = OpcionSerializer
