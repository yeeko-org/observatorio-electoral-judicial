from django.db import models
from django.db.models import JSONField


class State(models.Model):

    inegi_code = models.CharField(max_length=2, verbose_name=u"Clave INEGI")
    name = models.CharField(max_length=50, verbose_name=u"Nombre")
    short_name = models.CharField(
        max_length=20, verbose_name=u"Nombre Corto",
        blank=True, null=True)
    code_name = models.CharField(
        max_length=6, verbose_name=u"Nombre Clave",
        blank=True, null=True)
    circuit = models.IntegerField(
        verbose_name=u"Circuito electoral", blank=True, null=True)
    alternative_names = JSONField(
        default=list,
        verbose_name="Lista nombres alternativos",
        help_text="Ocupar para OCAMIS")

    def __str__(self):
        return self.short_name or self.name

    class Meta:
        ordering = ["inegi_code"]
        verbose_name = u"Estado"
        verbose_name_plural = u"Estados"
        db_table = "borde_state"


class Municipality(models.Model):

    inegi_code = models.CharField(max_length=6, verbose_name="Clave INEGI")
    complete_code = models.CharField(
        max_length=8, verbose_name="Clave INEGI Completa")
    name = models.CharField(max_length=255, verbose_name="Nombre")
    std_name = models.CharField(
        max_length=255, verbose_name="Nombre Estandarizado")
    state = models.ForeignKey(
        State, verbose_name="State",
        null=True, on_delete=models.CASCADE,
        related_name="municipalities")
    population = models.IntegerField(
        blank=True, null=True, verbose_name="Población")
    latitude = models.FloatField(
        blank=True, null=True, verbose_name="Latitud de cabecera")
    longitude = models.FloatField(
        blank=True, null=True, verbose_name="Longitud de cabecera")
    altitude = models.IntegerField(
        blank=True, null=True, verbose_name="Altitud de cabecera")

    def __str__(self):
        return "%s - %s" % (self.name, self.state)

    class Meta:
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        ordering = ["inegi_code"]
