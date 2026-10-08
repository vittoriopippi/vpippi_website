from django.urls import path

from . import api

app_name = "assistant_api"

urlpatterns = [
    path("tools/", api.list_tools, name="tools"),
    path("tools/<slug:name>/", api.call_tool, name="call_tool"),
    path("actions/", api.list_pending, name="pending"),
    path("actions/<int:pk>/confirm/", api.confirm_action, name="confirm_action"),
    path("actions/<int:pk>/cancel/", api.cancel_action, name="cancel_action"),
]
