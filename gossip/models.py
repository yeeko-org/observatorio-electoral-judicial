from django.db import models


class GossipResponse(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(
        max_length=255, blank=True, null=True)
    last_name = models.CharField(
        max_length=255, blank=True, null=True)
    state = models.CharField(
        max_length=255, blank=True, null=True)
    appointment = models.CharField(
        max_length=255, blank=True, null=True)
    source_type = models.CharField(
        max_length=255, blank=True, null=True)
    source_link = models.CharField(
        max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    email = models.CharField(
        max_length=255, blank=True, null=True)
    phone = models.CharField(
        max_length=255, blank=True, null=True)
    key = models.CharField(
        max_length=30, blank=True, null=True)
    valid_filled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        import random
        import string
        if not self.pk:
            self.key = ''.join([
                random.choice(string.ascii_letters + string.digits)
                for n in range(30)])
        else:
            self.key = ''
        super(GossipResponse, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Respuesta al Formulario'
        verbose_name_plural = 'Respuestas al Formulario'


def upload_to_gossip_file(instance, filename):
    return f'gossip_files/{instance.gossip_response.id}/{filename}'


class ResponseFile(models.Model):
    gossip_response = models.ForeignKey(
        GossipResponse, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=upload_to_gossip_file, max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name if self.file else 'Archivo sin nombre'

    class Meta:
        verbose_name = 'Archivo de Respuesta'
        verbose_name_plural = 'Archivos de Respuesta'
