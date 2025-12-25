from django.contrib import admin
from .models import Game, Team, Player, Card, GameRound

# Register your models here.

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('code', 'status', 'current_round', 'created_at')
    list_filter = ('status', 'current_round')
    search_fields = ('code',)
    readonly_fields = ('code', 'created_at')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('get_color_display', 'game', 'total_score', 'score_round1', 'score_round2', 'score_round3')
    list_filter = ('game', 'color')
    search_fields = ('game__code',)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'role')
    list_filter = ('role',)
    search_fields = ('name', 'team__name')

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'guessed_in_current_round')
    list_filter = ('game', 'guessed_in_current_round')
    search_fields = ('name', 'game__code')

@admin.register(GameRound)
class GameRoundAdmin(admin.ModelAdmin):
    list_display = ('game', 'round_number', 'team', 'card', 'guessed_at')
    list_filter = ('round_number', 'game')
    search_fields = ('game__code', 'team__name', 'card__name')
    readonly_fields = ('guessed_at',)
