from django.contrib import admin
from .models import Map, Interaction, Door, Player


class MapAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin_x', 'origin_y', 'origin_orientation', 'width', 'height')


admin.site.register(Map, MapAdmin)
admin.site.register(Interaction)
admin.site.register(Door)
admin.site.register(Player)
