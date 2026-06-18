from django.contrib import admin
from django.urls import path
from api import views

urlpatterns = [
    path('api/applications/', views.api_applications)
    , path('api/get_xcsrf/', views.api_get_xcsrf)
    , path('api/users/', views.api_users)
    , path('api/auth/', views.api_auth)
    , path('api/cars/', views.api_cars)
    , path('api/statuses/', views.api_statuses)
]