from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db.models import Q          #  NEW

from .models import Media
from .models import Acknowledgement, LinkAcknowledgement


class HasHTMLFilter(admin.SimpleListFilter):          #  NEW
    """Sidebar filter: Yes / No depending on whether `html` is meaningful."""
    title = "Has HTML?"
    parameter_name = "has_html"

    def lookups(self, request, model_admin):
        return (("yes", "Yes"), ("no", "No"))

    def queryset(self, request, queryset):
        value = self.value()
        # treat empty strings or the literal string "none" (case-insensitive) as “no”
        empty = Q(html__isnull=True) | Q(html__exact="") | Q(html__iexact="none")
        if value == "yes":
            return queryset.exclude(empty)
        if value == "no":
            return queryset.filter(empty)
        return queryset


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
        "has_html",          #  NEW – ✔ / ✘ flag
        "first_alt",
        "question",
        "password",
        "link_count",
    )
    search_fields = ("name_surname", "question", "html")
    list_filter = (HasHTMLFilter,)     #  NEW – sidebar filter
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

    # ---------- NEW ----------
    def has_html(self, obj):
        """Boolean check mark if html is not empty/‘none’."""
        return bool(obj.html and obj.html.strip().lower() != "none")

    has_html.boolean = True          # show ✔ / ✘ icons
    has_html.short_description = "Has HTML"
    has_html.admin_order_field = "html"
    # --------------------------

    def preview_html(self, obj):
        """Safely render the stored HTML for a quick preview inside the admin."""
        if not obj.html:
            return "(no HTML provided)"
        return format_html(
            '<div style="border:1px solid #ccc;padding:1rem;max-height:400px;overflow:auto;">{}</div>',
            obj.html,
        )

    preview_html.short_description = "Preview"

    def link_count(self, obj):
        return obj.links.count()

    link_count.short_description = "# Links"

    def first_alt(self, obj):
        return obj.first_alt

    first_alt.short_description = "First Alternative Name"


@admin.register(LinkAcknowledgement)
class LinkAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ("alt", "ack")
    search_fields = ("alt", "ack__name_surname")
    autocomplete_fields = ["ack"]


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ("title", "uploaded_at", "file_link")

    # handy download link right inside the changelist
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file.url)
        return "—"
    file_link.short_description = "File"
