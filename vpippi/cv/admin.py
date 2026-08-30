from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import CVVariant


class CVVariantAdminForm(forms.ModelForm):
    class Meta:
        model = CVVariant
        fields = '__all__'
        widgets = {
            'source_content': forms.Textarea(attrs={'rows': 35, 'style': 'font-family: monospace; width: 100%;'}),
        }


@admin.register(CVVariant)
class CVVariantAdmin(admin.ModelAdmin):
    form = CVVariantAdminForm
    list_display = ('label', 'slug', 'source_type', 'is_default', 'is_published', 'is_locked')
    list_filter = ('source_type', 'is_default', 'is_published', 'is_locked')
    search_fields = ('label', 'slug', 'source_content')
    prepopulated_fields = {'slug': ('label',)}
    readonly_fields = ('rendered_html_preview',)

    def rendered_html_preview(self, obj):
        if not obj.pk:
            return '(save to see the compiled result)'
        if obj.source_type == 'html':
            return '(shown as-is — no conversion for HTML sources)'
        if 'cv-latex-error' in obj.rendered_html:
            return mark_safe(obj.rendered_html)
        return mark_safe(
            '<div style="border:1px solid #ccc; padding:12px; max-height:400px; overflow:auto;">'
            + obj.rendered_html + '</div>'
        )
