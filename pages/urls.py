from django.urls import path
from pages import views

urlpatterns = [
    path("", views.home, name='home'),
    path("about_us/", views.about_us, name="about_us"),
    path("categories/", views.categories, name="categories"),
    path('country/<str:country_code>/', views.country_view, name='country_view'),
    path('compare_data/', views.compare_data, name='compare_data'),
    path("categories/<int:category_id>/", views.category_detail, name="category_detail"),
    path('heatmap/', views.heatmap_page_view, name='heatmap'),
    path('heatmap-data/', views.heatmap_data_view, name='heatmap-data'),
    path("heat-insight/<str:country_code>/", views.heat_insight_view, name="heat-insight"),
    path("rankings/", views.rankings_view, name="rankings"),
]
