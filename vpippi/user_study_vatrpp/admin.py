from django.contrib import admin
from user_study_vatrpp import models

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


class CompetitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'reference', 'winner', 'available', 'images_count', 'max_width', 'max_height')
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

class SampleImageAdmin(admin.ModelAdmin):
    list_display = ('competitor', 'img', 'exclude_from_study', 'iam_id')
    list_filter = ('competitor', 'exclude_from_study', 'iam_id')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('date', 'player', 'winner')

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('username', 'accuracy', 'answers_count', 'correct_control_answers', 'time_delta', 'created_at', 'finished', 'visible')
    list_filter = ('visible', 'correct_control_answers', 'finished', 'created_at')
    actions = [set_finished, set_not_finished]

    def answers_count(self, obj):
        return models.Answer.objects.filter(player=obj).count()
    answers_count.short_description = 'Answers'


admin.site.register(models.Competitor, CompetitorAdmin)
admin.site.register(models.SampleImage, SampleImageAdmin)
admin.site.register(models.Answer, AnswerAdmin)
admin.site.register(models.Player, PlayerAdmin)


