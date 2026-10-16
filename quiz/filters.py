import django_filters as filters

from .models import Pregunta


class PreguntaFilter(filters.FilterSet):
    """Filtro por examen (?examen=<id>) para el recurso de preguntas."""

    examen = filters.NumberFilter(field_name='examen__id')

    class Meta:
        model = Pregunta
        fields = ['examen']
