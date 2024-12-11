from django.urls import path
from .views import DashboardHomeView, DashboardProductHome, DashboardOrderHome, DashboardProductAdd, DashboardProductCategory, DashboardProductDisplay, DashboardProductInventory, DashboardProductList, DashboardProductOutofstock, DashboardConsumerHome, DashboardShopHome

urlpatterns = [
    path('home/', DashboardHomeView.as_view(), name='dashboard_home'),
    # 주문 관리
    path('order/home/', DashboardOrderHome.as_view(), name='dashboard_order_home'),
    # 임직원몰 관리
    path('shop/home/', DashboardShopHome.as_view(), name='dashboard_shop_home'),
    # 상품 관리
    path('product/home/', DashboardProductHome.as_view(), name='dashboard_product_home'),
    path('product/list/', DashboardProductList.as_view(), name='dashboard_product_list'),
    path('product/add/', DashboardProductAdd.as_view(), name='dashboard_product_add'),
    path('product/category/', DashboardProductCategory.as_view(), name='dashboard_product_category'),
    path('product/display/', DashboardProductDisplay.as_view(), name='dashboard_product_display'),
    path('product/inventory/', DashboardProductInventory.as_view(), name='dashboard_product_inventory'),
    path('product/out-of-stock/', DashboardProductOutofstock.as_view(), name='dashboard_product_outofstock'),
    # 고객 관리
    path('consumer/home/', DashboardConsumerHome.as_view(), name='dashboard_consumer_home'),
]