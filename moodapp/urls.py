from django.urls import path
from . import views

app_name = 'moodapp'

urlpatterns = [
    path('', views.index, name='index'),
]
