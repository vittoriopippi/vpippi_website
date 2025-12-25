from django.urls import path
from . import views

app_name = 'timesup'

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_game, name='create_game'),
    path('join/', views.join_game, name='join_game'),
    path('<str:code>/setup/', views.setup, name='setup'),
    path('<str:code>/lobby/', views.lobby, name='lobby'),
    path('<str:code>/start/<int:round_number>/', views.start_round, name='start_round'),
    path('<str:code>/play/', views.play, name='play'),
    path('<str:code>/get-card/', views.get_card, name='get_card'),
    path('<str:code>/card-guessed/', views.card_guessed, name='card_guessed'),
    path('<str:code>/undo-card/', views.undo_card, name='undo_card'),
    path('<str:code>/end-turn/', views.end_turn, name='end_turn'),
    path('<str:code>/round-complete/', views.round_complete, name='round_complete'),
    path('<str:code>/final-scores/', views.final_scores, name='final_scores'),
]
