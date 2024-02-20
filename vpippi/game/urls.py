from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<str:map_name>/", views.load_map, name="load_map"),
]