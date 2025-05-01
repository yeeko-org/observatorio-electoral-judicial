from django.contrib import admin

from .models import (
    Biography, StatusControl, Position, Seat, Candidate, ProfessionalLicense
)
from geo.models import Body, Power, Topic


@admin.register(Biography)
class BiographyAdmin(admin.ModelAdmin):
    pass


@admin.register(Body)
class BodyAdmin(admin.ModelAdmin):
    pass


@admin.register(StatusControl)
class StatusControlAdmin(admin.ModelAdmin):
    list_display = [
        "public_name", "name", "group", "order", "is_public", "color", "icon"]
    list_editable = ["order", "color", "icon"]
    list_filter = ["group"]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    pass


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    pass


@admin.register(Power)
class PowerAdmin(admin.ModelAdmin):
    pass


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    pass


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    pass


@admin.register(ProfessionalLicense)
class ProfessionalLicenseAdmin(admin.ModelAdmin):
    pass
