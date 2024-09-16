from django.contrib import admin
from user_study_mad import models

@admin.action(description="Enable selected competitors")
def enable_competitors(modeladmin, request, queryset):
    queryset.update(available=True)

@admin.action(description="Disable selected competitors")
def disable_competitors(modeladmin, request, queryset):
    queryset.update(available=False)

@admin.action(description="Invert answers")
def invert_answers(modeladmin, request, queryset):
    for player in queryset:
        answers = models.Answer.objects.filter(player=player)
        for answer in answers:
            answer.winner = answer.question.sample_a if answer.winner == answer.question.sample_b else answer.question.sample_b
            answer.save()
        player.update_accuracy()
        player.update_correct_control_answers()
        player.save()

@admin.action(description="Set finished to True")
def set_finished(modeladmin, request, queryset):
    queryset.update(finished=True)

@admin.action(description="Set finished to False")
def set_not_finished(modeladmin, request, queryset):
    queryset.update(finished=False)




class CompetitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'winner', 'available', 'images_count', 'questions_count', 'images_sizes')
    list_filter = ('winner', 'available')
    actions = [enable_competitors, disable_competitors]

    def images_count(self, obj):
        return models.SampleImage.objects.filter(competitor=obj).count()
    images_count.short_description = 'Images'

    def questions_count(self, obj):
        a_count = models.Question.objects.filter(sample_a__competitor=obj).count()
        b_count = models.Question.objects.filter(sample_b__competitor=obj).count()
        return a_count + b_count
    questions_count.short_description = 'Questions'
    
    def images_sizes(self, obj):
        return models.SampleImage.objects.filter(competitor=obj).first().width
    images_sizes.short_description = 'Sizes'

class SampleImageAdmin(admin.ModelAdmin):
    list_display = ('competitor', 'prompt', 'img', 'exclude_from_study')
    list_filter = ('competitor', 'prompt', 'exclude_from_study')

class PromptAdmin(admin.ModelAdmin):
    list_display = ('eng_text', 'ita_text')

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('sample_a', 'sample_b', 'is_control')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('date', 'player', 'winner', 'question')

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('username', 'accuracy', 'answers_count', 'correct_control_answers', 'time_delta', 'created_at', 'finished', 'visible', 'max_score')
    list_filter = ('visible', 'correct_control_answers', 'finished', 'created_at')
    actions = [invert_answers, set_finished, set_not_finished]

    def answers_count(self, obj):
        return models.Answer.objects.filter(player=obj).count()
    answers_count.short_description = 'Answers'


admin.site.register(models.Competitor, CompetitorAdmin)
admin.site.register(models.SampleImage, SampleImageAdmin)
admin.site.register(models.Prompt, PromptAdmin)
admin.site.register(models.Question, QuestionAdmin)
admin.site.register(models.Answer, AnswerAdmin)
admin.site.register(models.Player, PlayerAdmin)


