from django.contrib import admin

from .models import Invite

class InviteAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'state', 'date_created', 'date_modified')
    search_fields = ('name', 'phone', 'state')
    list_filter = ('state',)

admin.site.register(Invite, InviteAdmin)