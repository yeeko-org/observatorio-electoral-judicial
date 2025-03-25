from django.contrib import admin
from geo.models import (State, Municipality)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name"]


@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ["inegi_code", "name", "state"]
    search_fields = ["inegi_code", "name", "state"]
    list_filter = ["state"]
    raw_id_fields = ["state"]
