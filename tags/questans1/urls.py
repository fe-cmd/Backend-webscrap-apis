from django.urls import path
from . import views


from .views import extract1_data_api 

app_name = "questans1"

urlpatterns = [
    path('extract1-data/', views.extract1_data_api, name='extract1_data_api'),
]
