from django.db import models


class Examen(models.Model):
    """Un cuestionario compuesto por varias preguntas."""

    titulo = models.CharField('título', max_length=200)
    descripcion = models.TextField('descripción', blank=True)
    activo = models.BooleanField('activo', default=True)
    fecha_creacion = models.DateTimeField('fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'examen'
        verbose_name_plural = 'exámenes'
        ordering = ['id']

    def __str__(self):
        return self.titulo


class Pregunta(models.Model):
    """Pregunta de un examen; contiene varias opciones."""

    examen = models.ForeignKey(
        Examen,
        related_name='preguntas',
        on_delete=models.CASCADE,
        verbose_name='examen',
    )
    enunciado = models.TextField('enunciado')
    orden = models.PositiveIntegerField('orden', default=1)

    class Meta:
        verbose_name = 'pregunta'
        verbose_name_plural = 'preguntas'
        ordering = ['examen_id', 'orden', 'id']

    def __str__(self):
        return self.enunciado[:50]


class Opcion(models.Model):
    """Opción de respuesta de una pregunta."""

    pregunta = models.ForeignKey(
        Pregunta,
        related_name='opciones',
        on_delete=models.CASCADE,
        verbose_name='pregunta',
    )
    texto = models.CharField('texto', max_length=300)
    es_correcta = models.BooleanField('es correcta', default=False)

    class Meta:
        verbose_name = 'opción'
        verbose_name_plural = 'opciones'
        ordering = ['id']

    def __str__(self):
        return self.texto[:50]
