from django.db import models
from geo.models import State, Body, Power
from utils.common import text_normalizer


class Biography(models.Model):

    exp = models.CharField(max_length=80)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    full_name_normalized = models.CharField(
        max_length=255, blank=True, null=True)
    html_content = models.TextField(blank=True, null=True)
    curriculum = models.TextField(blank=True, null=True)
    ruta = models.CharField(max_length=80, blank=True, null=True)
    last_update = models.CharField(max_length=200, blank=True, null=True)
    recover_url = models.CharField(max_length=255, blank=True, null=True)
    recover_timestamp = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return (self.full_name or 'Biografía sin nombre') + ' - ' + self.exp

    def save(self, *args, **kwargs):
        if not self.full_name_normalized:
            self.full_name_normalized = text_normalizer(self.full_name)
        super(Biography, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Biografía'
        verbose_name_plural = 'Biografías'


GROUP_CHOICES = [
    ("register", "Registro"),
    ("validation", "Validación"),
    ("location", "Ubicación"),
]


class StatusControl(models.Model):
    name = models.CharField(max_length=120, primary_key=True)
    group = models.CharField(
        max_length=10, choices=GROUP_CHOICES,
        verbose_name="grupo de status", default="petition")
    public_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(
        max_length=30, blank=True, null=True,
        help_text="https://vuetifyjs.com/en/styles/colors/")
    icon = models.CharField(max_length=40, blank=True, null=True)
    order = models.IntegerField(default=4)
    is_public = models.BooleanField(default=True)
    open_editor = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.group} - {self.public_name}"

    class Meta:
        ordering = ["group", "order"]
        verbose_name = "Status de control"
        verbose_name_plural = "Status de control (TODOS)"


class Position(models.Model):
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    short_name = models.CharField(max_length=40, blank=True, null=True)
    male_name = models.CharField(max_length=255, blank=True, null=True)
    female_name = models.CharField(max_length=255, blank=True, null=True)
    body = models.ForeignKey(
        Body, on_delete=models.CASCADE, related_name='positions')
    sub_body = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_national = models.BooleanField(default=False)
    by_circuit = models.BooleanField(default=False)
    by_circunscription = models.BooleanField(
        default=False, verbose_name='Por circunscripción')
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.short_name or self.name

    class Meta:
        verbose_name = 'Posición'
        verbose_name_plural = 'Posiciones'


class Topic(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_mix = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'


class Seat(models.Model):
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, related_name='seats')
    state = models.ForeignKey(
        State, on_delete=models.CASCADE, blank=True, null=True,
        related_name='seats')
    circunscription = models.IntegerField(blank=True, null=True)
    topics = models.ManyToManyField(Topic, related_name='seats')

    def __str__(self):
        return f"{self.position} - {self.state} - {self.circunscription}"

    class Meta:
        verbose_name = 'Escaño'
        verbose_name_plural = 'Escaños'


class Candidate(models.Model):
    SEX_CHOICES = (
        ("Hombre", "Hombre"),
        ("Mujer", "Mujer"),
    )

    first_name = models.CharField(max_length=255)
    last_name_1 = models.CharField(max_length=255)
    last_name_2 = models.CharField(max_length=255, blank=True, null=True)
    first_name_normalized = models.CharField(
        max_length=255, blank=True, null=True)
    last_name_1_normalized = models.CharField(
        max_length=255, blank=True, null=True)
    last_name_2_normalized = models.CharField(
        max_length=255, blank=True, null=True)
    alternative_names = models.JSONField(blank=True, null=True)
    find_names = models.JSONField(blank=True, null=True)
    full_name_normalized = models.CharField(
        max_length=255, blank=True, null=True)
    seat = models.ForeignKey(
        Seat, on_delete=models.CASCADE, related_name='candidates')
    powers = models.ManyToManyField('geo.Power', related_name='candidates')
    biography = models.ForeignKey(
        Biography, on_delete=models.CASCADE, blank=True, null=True,
        related_name='candidates')
    first_year = models.SmallIntegerField(blank=True, null=True)
    sex = models.CharField(
        max_length=10, choices=SEX_CHOICES, blank=True, null=True)
    photo = models.FileField(
        upload_to='candidates_photos/', max_length=255, blank=True, null=True)
    gemini_link = models.URLField(blank=True, null=True)
    gemini_text = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    price_details = models.JSONField(blank=True, null=True)
    academic_ia = models.TextField(blank=True, null=True)
    academic_text = models.TextField(blank=True, null=True)
    professional_ia = models.TextField(blank=True, null=True)
    professional_text = models.TextField(blank=True, null=True)
    professional_summary = models.TextField(blank=True, null=True)
    more_info_ia = models.TextField(blank=True, null=True)
    more_info_text = models.TextField(blank=True, null=True)
    judgments = models.TextField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    attention_notes_ia = models.TextField(blank=True, null=True)
    sources = models.JSONField(blank=True, null=True)
    is_public = models.BooleanField(default=False)

    status_register = models.ForeignKey(
        StatusControl, on_delete=models.CASCADE, blank=True, null=True,
        related_name='candidates_practica')
    status_validation = models.ForeignKey(
        StatusControl, on_delete=models.CASCADE, blank=True, null=True,
        related_name='candidates_laboratorio')

    def save(self, *args, **kwargs):
        if not self.first_name_normalized:
            self.first_name_normalized = text_normalizer(self.first_name)
        if not self.last_name_1_normalized:
            self.last_name_1_normalized = text_normalizer(self.last_name_1)
        if not self.last_name_2_normalized:
            self.last_name_2_normalized = text_normalizer(self.last_name_2)
        if not self.full_name_normalized:
            full_name = f"{self.first_name} {self.last_name_1} {self.last_name_2}"
            full_name = full_name.strip()
            self.full_name_normalized = text_normalizer(full_name)
        super(Candidate, self).save(*args, **kwargs)

    @property
    def position(self):
        pos = self.seat.position
        sub_body = self.seat.position.sub_body or ''
        if sub_body:
            sub_body = f"de la {sub_body} "
        gender_prefix = pos.female_name if self.sex == "Mujer" \
            else pos.male_name
        return f"{gender_prefix} {sub_body}{pos.name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name_1}"

    class Meta:
        verbose_name = 'Candidato'
        verbose_name_plural = 'Candidatos'


class ProfessionalLicense(models.Model):
    id_licence = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name='Número de Cédula Profesional')
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name='licenses')
    title = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name='Título completo')
    level = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Nivel')
    career = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Profesión')
    institution = models.CharField(max_length=255, blank=True, null=True)
    licence_type = models.CharField(max_length=255, blank=True, null=True)
    year = models.SmallIntegerField(
        blank=True, null=True, verbose_name='Año de expedición')
    other_data = models.JSONField(
        blank=True, null=True, verbose_name='Datos base')
    is_exact = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return f"{self.id_licence or 'S/NUM'} - {self.title or 'Sin carrera'}"

    class Meta:
        verbose_name = 'Licencia Profesional'
        verbose_name_plural = 'Licencias Profesionales'
