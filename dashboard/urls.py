from django.urls import path
from .views import DashboardHomeView

urlpatterns = [
    path('home/', DashboardHomeView.as_view(), name='dashboard_home'),
]