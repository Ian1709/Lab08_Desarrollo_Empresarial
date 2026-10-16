from django.db import transaction
from rest_framework import serializers

from .models import Examen, Opcion, Pregunta


class OpcionSerializer(serializers.ModelSerializer):
    """Opción de respuesta como recurso independiente (/api/opciones/).

    Incluye ``pregunta`` (referida por identificador) para poder crear y
    editar opciones sueltas.
    """

    class Meta:
        model = Opcion
        fields = ['id', 'pregunta', 'texto', 'es_correcta']
        read_only_fields = ['id']


class OpcionAnidadaSerializer(serializers.ModelSerializer):
    """Opción anidada dentro de una pregunta.

    No expone ``pregunta``: la relación la fija el serializador de la
    pregunta que la contiene.
    """

    class Meta:
        model = Opcion
        fields = ['id', 'texto', 'es_correcta']
        read_only_fields = ['id']


class PreguntaSerializer(serializers.ModelSerializer):
    """Pregunta con sus opciones anidadas.

    El examen se refiere por identificador (``examen`` es un
    ``PrimaryKeyRelatedField`` que DRF construye a partir del modelo).
    Las opciones viajan anidadas y son escribibles.
    """

    opciones = OpcionAnidadaSerializer(many=True)

    class Meta:
        model = Pregunta
        fields = ['id', 'examen', 'enunciado', 'orden', 'opciones']
        read_only_fields = ['id']

    def validate(self, attrs):
        """No se acepta una pregunta sin exactamente una opción correcta."""
        if 'opciones' in attrs:
            correctas = sum(
                1 for opcion in attrs['opciones'] if opcion.get('es_correcta')
            )
        elif self.instance is not None:
            # Actualización parcial sin tocar las opciones: se cuentan las
            # que ya están guardadas.
            correctas = self.instance.opciones.filter(es_correcta=True).count()
        else:
            correctas = 0

        if correctas != 1:
            raise serializers.ValidationError(
                {
                    'opciones': (
                        'La pregunta debe tener exactamente una opción '
                        f'correcta (se recibieron {correctas}).'
                    )
                }
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        opciones_data = validated_data.pop('opciones', [])
        pregunta = Pregunta.objects.create(**validated_data)
        for opcion_data in opciones_data:
            Opcion.objects.create(pregunta=pregunta, **opcion_data)
        return pregunta

    @transaction.atomic
    def update(self, instance, validated_data):
        opciones_data = validated_data.pop('opciones', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if opciones_data is not None:
            # Se reemplazan las opciones por las enviadas.
            instance.opciones.all().delete()
            for opcion_data in opciones_data:
                Opcion.objects.create(pregunta=instance, **opcion_data)
        return instance


class ExamenSerializer(serializers.ModelSerializer):
    """Examen. Las preguntas se consultan por su propio recurso
    (``/api/preguntas/?examen=<id>``), no se anidan aquí."""

    class Meta:
        model = Examen
        fields = ['id', 'titulo', 'descripcion', 'activo', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']
