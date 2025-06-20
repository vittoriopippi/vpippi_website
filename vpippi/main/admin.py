from django.contrib import admin
from .models import Author, Tag, Conference, Paper, Authorship

class AuthorshipInline(admin.TabularInline):
    model = Authorship
    extra = 1
    autocomplete_fields = ['author']
    ordering = ['order']

@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'conference', 'publication_date')
    list_filter = ('conference', 'tags')
    search_fields = ('title', 'abstract')
    inlines = [AuthorshipInline]
    date_hierarchy = 'publication_date'
    filter_horizontal = ('tags',)

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'scholar_url')
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'url')
    search_fields = ('name', 'short_name')
