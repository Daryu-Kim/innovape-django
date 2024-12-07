from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
from .views import login_check_view, get_access_naver_info, get_access_coupang_info, get_access_interpark_info, get_access_sixshop_info, get_access_cafe24_info, get_cafe24_auth_code, smartstore_product_upload

urlpatterns = [
  path('', login_check_view, name='login_check'),
  path('admin/', admin.site.urls),
  path('account/', include('account.urls')),
  path('dashboard/', include('dashboard.urls')),
  path('get-access-naver-info', get_access_naver_info, name='get_access_naver_info'),
  path('get-access-coupang-info', get_access_coupang_info, name='get_access_coupang_info'),
  path('get-access-interpark-info', get_access_interpark_info, name='get_access_interpark_info'),
  path('get-access-sixshop-info', get_access_sixshop_info, name='get_access_sixshop_info'),
  path('get-access-cafe24-info', get_access_cafe24_info, name='get_access_cafe24_info'),
  path('get-cafe24-auth-code', get_cafe24_auth_code, name='get_cafe24_auth_code'),
  path('smartstore-product-upload', smartstore_product_upload, name='smartstore_product_upload'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
