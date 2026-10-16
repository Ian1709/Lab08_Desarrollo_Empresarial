from rest_framework import viewsets

from .filters import PreguntaFilter
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
    """CRUD de preguntas: /api/preguntas/

    Filtrado por examen (?examen=<id>) y búsqueda por enunciado
    (?search=<texto>).
    """

    queryset = Pregunta.objects.select_related('examen').prefetch_related('opciones')
    serializer_class = PreguntaSerializer
    filterset_class = PreguntaFilter
    search_fields = ['enunciado']


class OpcionViewSet(viewsets.ModelViewSet):
    """CRUD de opciones: /api/opciones/"""

    queryset = Opcion.objects.select_related('pregunta')
    serializer_class = OpcionSerializer
