from django.urls import path
from web_interface import views


# path.register(r'news', views.NewsViewSet)

urlpatterns = [
    path('', views.SearchView.as_view(), name='search'),
    path('fetch/<int:pk>/', views.FetchView.as_view(), name='fetch')
]
