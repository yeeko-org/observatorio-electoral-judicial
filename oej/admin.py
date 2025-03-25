from django.contrib import admin

from .models import (
    Biography, Body, StatusControl, Position, Topic, Power, ElectoralDistrict,
    Seat, Candidate, ProfessionalLicense
)


@admin.register(Biography)
class BiographyAdmin(admin.ModelAdmin):
    pass


@admin.register(Body)
class BodyAdmin(admin.ModelAdmin):
    pass


@admin.register(StatusControl)
class StatusControlAdmin(admin.ModelAdmin):
    pass


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    pass


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    pass


@admin.register(Power)
class PowerAdmin(admin.ModelAdmin):
    pass


@admin.register(ElectoralDistrict)
class ElectoralDistrictAdmin(admin.ModelAdmin):
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
