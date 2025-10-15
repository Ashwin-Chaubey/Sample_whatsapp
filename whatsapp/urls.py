from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('send/', views.send_whatsapp, name='send'),
    path('webhook/', views.webhook, name='webhook'),
    path('get-status/', views.get_status, name='get_status'),
    path('get-all-statuses/', views.get_all_statuses, name='get_all_statuses'),
    path('get-incoming-messages/', views.get_incoming_messages, name='get_incoming_messages'),
]