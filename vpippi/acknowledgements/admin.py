from django.contrib import admin
from .models import Acknowledgement, LinkAcknowledgement, FakeAcknowledgement

@admin.register(Acknowledgement)
class AcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('name_surname', 'text')
    search_fields = ('name_surname',)
    ordering = ('name_surname',)

@admin.register(LinkAcknowledgement)
class LinkAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('alt', 'ack')
    search_fields = ('alt',)

@admin.register(FakeAcknowledgement)
class FakeAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('text',)
