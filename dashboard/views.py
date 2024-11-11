from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

# Create your views here.
class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'  # 사용할 템플릿 파일 지정
    login_url = reverse_lazy('account_login')

class DashboardOrderHome(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/order/order_home.html'
    login_url = reverse_lazy('account_login')

class DashboardProductHome(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/product/product_home.html'
    login_url = reverse_lazy('account_login')

