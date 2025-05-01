from django.db import models
from django.db.models import JSONField


class Circunscription(models.Model):

    name = models.CharField(max_length=255)
    number = models.IntegerField()
    city = models.CharField(
        max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.number} - {self.city}"

    class Meta:
        verbose_name = 'Circunscripción'
        verbose_name_plural = 'Circunscripciones'
        db_table = "oej_circunscription"


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
    circunscription = models.ForeignKey(
        Circunscription, on_delete=models.CASCADE, blank=True, null=True,
        related_name='states')

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


class Body(models.Model):

    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=40, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.short_name or self.name

    class Meta:
        verbose_name = 'Órgano'
        verbose_name_plural = 'Órganos'
        db_table = "oej_body"


class Power(models.Model):
    key_name = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=90)
    description = models.TextField(blank=True, null=True)
    icon_image = models.FileField(
        upload_to='oej_icons', max_length=255, blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=80, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Poder'
        verbose_name_plural = 'Poderes'
        db_table = "oej_power"


class JudicialElectoralDistrict(models.Model):
    circuit = models.IntegerField(
        verbose_name=u"Circuito electoral", blank=True, null=True)
    number = models.IntegerField()
    # federal_district = models.IntegerField(
    #     verbose_name="Distrito electoral", blank=True, null=True)
    state = models.ForeignKey(
        State, on_delete=models.CASCADE, blank=True, null=True,
        related_name='judicial_electoral_districts')
    second_state = models.ForeignKey(
        State, on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='judicial_electoral_districts_2')

    def __str__(self):
        return f"{self.number} - {self.circuit}"

    class Meta:
        unique_together = ('circuit', 'number')
        verbose_name = 'Distrito Electoral Judicial'
        verbose_name_plural = 'Distritos Electorales Judiciales'


class Section(models.Model):
    number = models.IntegerField()
    judicial_electoral_district = models.ForeignKey(
        JudicialElectoralDistrict, on_delete=models.CASCADE,
        related_name='sections')
    federal_district = models.IntegerField(
        verbose_name="Distrito electoral", blank=True, null=True)

    def __str__(self):
        return f'{self.judicial_electoral_district} - {self.number}'

    class Meta:
        verbose_name = 'Sección'
        verbose_name_plural = 'Secciones'


class Topic(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=40, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'


class Anomaly(models.Model):
    key_name = models.CharField(max_length=80, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Anomalía'
        verbose_name_plural = 'Anomalías'

