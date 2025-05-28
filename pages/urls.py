from django.urls import path
from pages import views

urlpatterns = [
    path("", views.home, name='home'),
    path("categories/", views.categories, name="categories"),
    path('country/<str:country_code>/', views.country_view, name='country_view'),
    path('compare_data/', views.compare_data, name='compare_data'),
    path("categories/<int:category_id>/", views.category_detail, name="category_detail"),
    path('heatmap/', views.heatmap_page_view, name='heatmap'),
    path('heatmap-data/', views.heatmap_data_view, name='heatmap-data'),
    path("about/", views.about_view, name="about"),


]
