from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.contrib import messages

class LoginView(TemplateView):
    template_name = 'account/login.html'  # 사용할 템플릿 파일 지정
    
    def post(self, request, *args, **kwargs):
      username = request.POST.get('username')
      password = request.POST.get('password')
      
      user = authenticate(request, username=username, password=password)
      if user is not None:
          login(request, user)
          return JsonResponse({'success': True, 'redirect_url': '/dashboard/home'} )  # 로그인 성공 시 리다이렉트할 URL
      else:
          return JsonResponse({'success': False, 'message': '로그인에 실패했습니다. 아이디와 비밀번호를 확인하세요.'})