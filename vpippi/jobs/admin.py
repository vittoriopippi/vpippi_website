from django.contrib import admin

from .models import JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'status', 'location', 'applied_date', 'updated_at')
    list_filter = ('status',)
    search_fields = ('title', 'company', 'location', 'notes')
