from django.contrib import admin
from user_study_emuru import models

@admin.action(description="Enable selected competitors")
def enable_competitors(modeladmin, request, queryset):
    queryset.update(available=True)

@admin.action(description="Disable selected competitors")
def disable_competitors(modeladmin, request, queryset):
    queryset.update(available=False)

@admin.action(description="Set finished to True")
def set_finished(modeladmin, request, queryset):
    queryset.update(finished=True)

@admin.action(description="Set finished to False")
def set_not_finished(modeladmin, request, queryset):
    queryset.update(finished=False)

@admin.action(description="Exclude selected images from study")
def exclude_from_study(modeladmin, request, queryset):
    shtg_keys = queryset.values_list('shtg_key', flat=True)
    models.SampleImage.objects.filter(shtg_key__in=shtg_keys).update(available=False)

class CompetitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'reference', 'winner', 'available', 'images_count', 'max_width', 'max_height', 'max_ratio')
    list_filter = ('winner', 'available')
    actions = [enable_competitors, disable_competitors]

    def images_count(self, obj):
        return models.SampleImage.objects.filter(competitor=obj).count()
    images_count.short_description = 'Images'

    def max_width(self, obj):
        return max([img.size[0] for img in models.SampleImage.objects.filter(competitor=obj)])
    max_width.short_description = 'Max width'

    def max_height(self, obj):
        return max([img.size[1] for img in models.SampleImage.objects.filter(competitor=obj)])
    max_height.short_description = 'Max height'

    def max_ratio(self, obj):
        return max([img.size[0] / img.size[1] for img in models.SampleImage.objects.filter(competitor=obj)])
    max_ratio.short_description = 'Max ratio'

class SampleImageAdmin(admin.ModelAdmin):
    list_display = ('competitor', 'img', 'available', 'shtg_key')
    list_filter = ('competitor', 'available', 'shtg_key')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('date', 'player', 'winner')

class SkippedAdmin(admin.ModelAdmin):
    list_display = ('date', 'player', 'shtg_key')
    actions = [exclude_from_study]

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('username', 'accuracy', 'answers_count', 'time_delta', 'created_at', 'finished', 'visible')
    list_filter = ('visible', 'finished', 'created_at')
    actions = [set_finished, set_not_finished]

    def answers_count(self, obj):
        return models.Answer.objects.filter(player=obj).count()
    answers_count.short_description = 'Answers'


admin.site.register(models.Competitor, CompetitorAdmin)
admin.site.register(models.SampleImage, SampleImageAdmin)
admin.site.register(models.Answer, AnswerAdmin)
admin.site.register(models.Player, PlayerAdmin)
admin.site.register(models.Skipped, SkippedAdmin)


