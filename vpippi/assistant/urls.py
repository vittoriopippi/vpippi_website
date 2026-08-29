from django.urls import path

from . import views

app_name = "assistant"

urlpatterns = [
    path("", views.chat_view, name="chat"),
    path("new/", views.new_session, name="new_session"),
    path("send/", views.send_message, name="send"),
    path("sessions/<int:pk>/model/", views.set_model, name="set_model"),
    path("actions/<int:pk>/confirm/", views.confirm_action, name="confirm_action"),
    path("actions/<int:pk>/cancel/", views.cancel_action, name="cancel_action"),
]
