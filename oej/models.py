from django.db import models
from geo.models import State, Body, Power, Circunscription
from utils.common import text_normalizer
from django.core.files.base import ContentFile
from profile_auth.models import User


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
    total_seats = models.IntegerField(
        default=0, verbose_name='Número de cargos')
    total_candidates = models.IntegerField(
        default=0, verbose_name='Número de cargos')
    color = models.CharField(
        max_length=30, blank=True, null=True)
    color_light  = models.CharField(
        max_length=30, blank=True, null=True)
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
    circunscription = models.ForeignKey(
        Circunscription, on_delete=models.CASCADE, blank=True, null=True,
        related_name='seats')
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

    id_ine = models.IntegerField(blank=True, null=True)
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
    full_name = models.CharField(
        max_length=255, blank=True, null=True)
    full_name_normalized = models.CharField(
        max_length=255, blank=True, null=True)
    seat = models.ForeignKey(
        Seat, on_delete=models.CASCADE, related_name='candidates')
    powers = models.ManyToManyField('geo.Power', related_name='candidates')

    sex = models.CharField(
        max_length=10, choices=SEX_CHOICES, blank=True, null=True)
    biography = models.ForeignKey(
        Biography, on_delete=models.CASCADE, blank=True, null=True,
        related_name='candidates')
    photo = models.FileField(
        upload_to='candidates_photos/', max_length=255, blank=True, null=True)
    photo_small = models.FileField(
        upload_to='candidates_photos/', max_length=255, blank=True, null=True)

    gemini_link = models.URLField(blank=True, null=True)
    gemini_text = models.TextField(blank=True, null=True)
    first_year = models.SmallIntegerField(blank=True, null=True)
    academic_ia = models.TextField(blank=True, null=True)
    academic_text = models.TextField(blank=True, null=True)
    professional_ia = models.TextField(blank=True, null=True)
    professional_text = models.TextField(blank=True, null=True)
    professional_summary = models.TextField(blank=True, null=True)
    more_info_ia = models.TextField(blank=True, null=True)
    more_info_text = models.TextField(blank=True, null=True)
    judgments = models.TextField(blank=True, null=True)
    attention_notes_ia = models.TextField(blank=True, null=True)
    sources = models.JSONField(blank=True, null=True)
    other_sources = models.TextField(blank=True, null=True)

    ine_data = models.JSONField(
        blank=True, null=True, verbose_name='Datos INE')
    ine_cv = models.URLField(
        blank=True, null=True, verbose_name='URL del CV INE')
    ine_cv_text = models.TextField(
        blank=True, null=True, verbose_name='Texto del CV INE')
    ine_photo = models.URLField(
        blank=True, null=True, verbose_name='URL de la foto del INE')
    num_list = models.CharField(
        max_length=4, blank=True, null=True,
        verbose_name='Número de lista')

    is_public = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)
    status_register = models.ForeignKey(
        StatusControl, on_delete=models.CASCADE, blank=True, null=True,
        related_name='candidates_practica')
    status_validation = models.ForeignKey(
        StatusControl, on_delete=models.CASCADE, blank=True, null=True,
        related_name='candidates_laboratorio')
    user_register = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True,
        related_name='candidates_register')
    user_validation = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True,
        related_name='candidates_validation')

    price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    price_details = models.JSONField(blank=True, null=True)

    @property
    def position(self):
        pos = self.seat.position
        sub_body = self.seat.position.sub_body or ''
        if sub_body:
            sub_body = f"de la {sub_body} "
        gender_prefix = pos.female_name if self.sex == "Mujer" \
            else pos.male_name
        return f"{gender_prefix} {sub_body}{pos.name}"

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
        if not self.full_name:
            full_name = f"{self.first_name} {self.last_name_1} {self.last_name_2}"
            self.full_name = full_name.strip()
        # if self.ine_photo and (not self.photo or not self.photo_small):
        #     self.save_image_from_url()
        super(Candidate, self).save(*args, **kwargs)

    def get_photo_content(self):
        import requests
        if self.photo:
            return self.photo.read()
        elif self.ine_photo:
            response = requests.get(self.ine_photo)
            if response.status_code == 200:
                image_content = response.content
                file_name = self.ine_photo.split("/")[-1]
                self.photo.save(
                    file_name, ContentFile(image_content), save=False)
                return image_content
            else:
                raise Exception(
                    f"Error al descargar la imagen. Código de estado: "
                    f"{response.status_code}"
                )
        else:
            return None

    def save_image_from_url(self):
        if not self.ine_photo:
            return
        image_content = None
        if not self.photo:
            image_content = self.get_photo_content()

        if not self.photo_small:
            self.save_small_image(image_content)

    def save_small_image(self, image_content):
        from PIL import Image, ImageDraw
        from io import BytesIO

        if not image_content:
            image_content = self.get_photo_content()
            if not image_content:
                return

        # Open the image
        img = Image.open(BytesIO(image_content))

        # Get original dimensions
        width, height = img.size

        # Set maximum width to 200px and calculate height to maintain aspect ratio
        max_width = 200
        new_height = int(height * (max_width / width))

        try:
            # Resize the image
            img_small = img.resize((max_width, new_height), Image.LANCZOS)

            # Make the image square (needed for a perfect circle)
            size = min(max_width, new_height)

            # Calculate offsets to crop from center
            left = (max_width - size) // 2
            top = (new_height - size) // 2
            right = left + size
            bottom = top + size

            # Crop to square
            img_small = img_small.crop((left, top, right, bottom))

            # Create a circular mask
            mask = Image.new('L', (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)

            # Create a transparent background image
            result = Image.new('RGBA', (size, size), (0, 0, 0, 0))

            # Convert the resized image to RGBA if it isn't already
            if img_small.mode != 'RGBA':
                img_small = img_small.convert('RGBA')

            # Paste the square image onto the result using the circular mask
            result.paste(img_small, (0, 0), mask)

            # Save as PNG
            output = BytesIO()
            result.save(output, format='PNG')
            output.seek(0)

            # Extract base filename and change extension to png
            original_filename = self.ine_photo.split('/')[-1]
            base_filename = original_filename.rsplit('.', 1)[0]  # Remove extension
            photo_small_name = f"small_{base_filename}.png"

            self.photo_small.save(
                photo_small_name, ContentFile(output.getvalue()), save=False)

            print(f"Imagen guardada exitosamente como {photo_small_name}.")
        except Exception as e:
            print(f"Error al procesar la imagen: {e}")

    def save_image_from_url_old(self):
        from PIL import Image
        from io import BytesIO

        if not self.ine_photo:
            return

        image_content = self.get_photo_content()
        if not image_content:
            return
        img = Image.open(BytesIO(image_content))
        # Get original dimensions
        width, height = img.size

        # Set maximum width to 100px and calculate height to maintain aspect ratio
        max_width = 200
        new_height = int(height * (max_width / width))
        try:
            img_small = img.resize((max_width, new_height), Image.LANCZOS)

            if img_small.mode == 'RGBA':
                img_small = img_small.convert('RGB')
            output = BytesIO()
            img_small.save(output, format='JPEG', quality=85)
            output.seek(0)
            file_name = self.ine_photo.split('/')[-1]
            photo_small_name = f"small_{file_name}"
            self.photo_small.save(
                photo_small_name, ContentFile(output.getvalue()), save=False)

            print(f"Imagen guardada exitosamente como {file_name}.")
        except Exception as e:
            print(f"Error al procesar la imagen: {e}")

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
