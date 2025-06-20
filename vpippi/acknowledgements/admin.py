from django.contrib import admin
from django import forms
from django.utils.html import format_html

from .models import Acknowledgement, LinkAcknowledgement


class AcknowledgementAdminForm(forms.ModelForm):
    """Admin form that hides the password behind a password input."""

    password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),  # show **** but keep value
        help_text="Password for accessing the acknowledgement (stored as-is).",
    )

    class Meta:
        model = Acknowledgement
        fields = "__all__"


class LinkAcknowledgementInline(admin.TabularInline):
    model = LinkAcknowledgement
    extra = 1
    autocomplete_fields = ["ack"]


@admin.register(Acknowledgement)
class AcknowledgementAdmin(admin.ModelAdmin):
    form = AcknowledgementAdminForm

    list_display = (
        "name_surname",
        "question",
        "link_count",
    )
    search_fields = ("name_surname", "question", "html")
    readonly_fields = ("preview_html",)

    fieldsets = (
        (None, {
            "fields": ("name_surname", "question", "password")
        }),
        ("Acknowledgement Text", {
            "fields": ("html", "preview_html"),
            "description": "Raw HTML and a rendered preview below.",
        }),
    )

    inlines = [LinkAcknowledgementInline]

    def preview_html(self, obj):
        """Safely render the stored HTML for a quick preview inside the admin."""
        if not obj.html:
            return "(no HTML provided)"
        return format_html('<div style="border:1px solid #ccc;padding:1rem;max-height:400px;overflow:auto;">{}</div>', obj.html)

    preview_html.short_description = "Preview"

    def link_count(self, obj):
        return obj.links.count()

    link_count.short_description = "# Links"


@admin.register(LinkAcknowledgement)
class LinkAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ("alt", "ack")
    search_fields = ("alt", "ack__name_surname")
    autocomplete_fields = ["ack"]
