from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.
class DashboardHomeView(TemplateView):
    template_name = 'dashboard/home.html'  # 사용할 템플릿 파일 지정