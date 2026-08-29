from django.urls import path

from . import views

app_name = "cv"

urlpatterns = [
    path("", views.default_cv, name="default"),
    path("cv/<slug:slug>/", views.cv_variant, name="variant"),
]
