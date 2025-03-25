from django.contrib import admin

from gossip.models import GossipResponse, ResponseFile


class ResponseFileInline(admin.TabularInline):
    model = ResponseFile
    extra = 0


@admin.register(GossipResponse)
class GossipResponseAdmin(admin.ModelAdmin):
    inlines = [ResponseFileInline]
    list_display = ['date', 'appointment', 'source_type']
    ordering = ['date']

