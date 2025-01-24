from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login, name="login"),
    path("scoreboard", views.scoreboard, name="scoreboard"),
    path("post_answer", views.post_answer, name="post_answer"),
    path("upload_question", views.upload_question, name="upload_question"),
    path("delete_all", views.delete_all, name="delete_all"),
    path("delete_competitors", views.delete_competitors, name="delete_competitors"),
    path("dump_answers", views.dump_answers, name="dump_answers"),
    path("update_players", views.update_players, name="update_players"),
    path("stats", views.stats, name="stats"),
]