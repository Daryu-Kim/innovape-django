from django.urls import path
from .views import DashboardHomeView, DashboardProductHome, DashboardOrderHome

urlpatterns = [
    path('home/', DashboardHomeView.as_view(), name='dashboard_home'),
    # 주문 관리
    path('order/home/', DashboardOrderHome.as_view(), name='dashboard_order_home'),
    # 상품 관리
    path('product/home/', DashboardProductHome.as_view(), name='dashboard_product_home'),
]