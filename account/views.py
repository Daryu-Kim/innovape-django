from django.contrib.auth.views import LoginView

class LoginView(LoginView):
    template_name = 'account/login.html'  # 사용할 템플릿 파일 지정