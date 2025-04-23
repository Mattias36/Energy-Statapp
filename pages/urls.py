from django.urls import path
from pages import views

urlpatterns = [
    path("", views.home, name='home'),
    path('country/<str:country_code>/', views.country_view, name='country_view') # np. link http://127.0.0.1:8000/country/PL/
]
