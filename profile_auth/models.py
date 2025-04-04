from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=100, blank=True)
    initials = models.CharField(
        max_length=10, blank=True, null=True,
        help_text='Iniciales del usuario')
    color = models.CharField(
        max_length=30, blank=True, null=True,
        help_text='Color del usuario')
    organization = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='Organización del usuario')
    full_editor = models.BooleanField(
        default=False, verbose_name='Es revisor',
        help_text='Puede editar cualquier contenido')

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name or self.last_name:
            return f"{self.first_name or self.last_name}"
        return self.username or self.email

    @property
    def is_full_editor(self):
        return self.is_superuser or self.full_editor


