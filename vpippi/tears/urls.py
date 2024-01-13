from django.urls import path

from . import views

urlpatterns = [
    path("<str:username>/create/", views.create, name="tears_create"),
    path("", views.index, name="index"),
    path("<str:username>", views.index, name="tears_index"),
]