from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='party_index'),
    path('list/', views.list, name='list'),
    path('make_invite/', views.make_invite, name='make_invite'),
    path('invite/<str:code>/', views.invite, name='invite'),
    path('invite/phone/<str:phone>/', views.from_phone, name='from_phone'),
]