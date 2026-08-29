from django import forms
from django.contrib import admin

from .models import CVVariant


class CVVariantAdminForm(forms.ModelForm):
    class Meta:
        model = CVVariant
        fields = '__all__'
        widgets = {
            'content_md': forms.Textarea(attrs={'rows': 35, 'style': 'font-family: monospace; width: 100%;'}),
        }


@admin.register(CVVariant)
class CVVariantAdmin(admin.ModelAdmin):
    form = CVVariantAdminForm
    list_display = ('label', 'slug', 'is_default', 'is_published', 'is_locked')
    list_filter = ('is_default', 'is_published', 'is_locked')
    search_fields = ('label', 'slug', 'content_md')
    prepopulated_fields = {'slug': ('label',)}
