from django.urls import path

from . import views

app_name = "cv"

urlpatterns = [
    path("", views.default_cv, name="default"),
    path("pdf/", views.default_cv_pdf, name="default_pdf"),
    path("cv/<slug:slug>/", views.cv_variant, name="variant"),
    path("cv/<slug:slug>/pdf/", views.variant_cv_pdf, name="variant_pdf"),
]
