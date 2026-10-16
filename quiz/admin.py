from django.contrib import admin

from .models import Examen, Opcion, Pregunta


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 1


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'activo', 'fecha_creacion')
    list_filter = ('activo',)
    search_fields = ('titulo', 'descripcion')


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('id', 'examen', 'enunciado', 'orden')
    list_filter = ('examen',)
    search_fields = ('enunciado',)
    inlines = [OpcionInline]


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ('id', 'pregunta', 'texto', 'es_correcta')
    list_filter = ('es_correcta',)
    search_fields = ('texto',)
