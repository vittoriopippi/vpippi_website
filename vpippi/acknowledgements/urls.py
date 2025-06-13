from django.urls import path
from .views import AcknowledgementView

urlpatterns = [
    path('', AcknowledgementView.as_view(), name='index'),
]
