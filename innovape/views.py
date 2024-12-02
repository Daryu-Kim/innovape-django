from urllib.parse import urlencode
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.http import JsonResponse
from decouple import config
from datetime import datetime
import time
import bcrypt
import pybase64
import requests
import base64


def login_check_view(request):
    if request.user.is_authenticated:
        return redirect("/dashboard/home")
    else:
        return redirect("/account/login")


def get_access_naver_info(request):
    client_id = config("NAVER_COMMERCE_ID")
    cilent_secret = config("NAVER_COMMERCE_SECRET")
    timestamp = int(time.time() * 1000)

    password = client_id + "_" + str(timestamp)
    hashed = bcrypt.hashpw(password.encode("utf-8"), cilent_secret.encode("utf-8"))
    encode_hashed = pybase64.standard_b64encode(hashed).decode("utf-8")

    data = {
        "client_id": client_id,
        "timestamp": timestamp,
        "grant_type": "client_credentials",
        "client_secret_sign": encode_hashed,
        "type": "SELF",
    }

    url = "https://api.commerce.naver.com/external/v1/oauth2/token"

    response = requests.post(url, data=data)
    if response.status_code == 200:
        return JsonResponse({"status": "success", "data": response.json()})
    else:
        return JsonResponse({"status": "error", "data": response.json()})


def get_access_coupang_info(request):
    expires = datetime.strptime(config("COUPANG_SECRET_KEY_EXPIRES"), "%Y-%m-%d %H:%M")
    now = datetime.now()

    if expires > now:
        difference = expires - now
        days_left = difference.days
        return JsonResponse({"status": "success", "data": days_left})
    else:
        return JsonResponse({"status": "error", "data": 0})


def get_access_interpark_info(request):
    # 인증키 발급 승인 후 개발 필요
    return JsonResponse({"status": "error", "data": None})


def get_access_sixshop_info(request):
    return JsonResponse({"status": "success", "data": None})

    # Selenium 가능 환경에서 재개발 필요.
    # service = Service('') # '' 안에 서버에서 사용할 크롬 드라이버 경로를 넣어줘야함.

    # options = Options()
    # options.add_argument('--headless')  # 헤드리스 모드
    # options.add_argument('--no-sandbox')  # 샌드박스 모드 비활성화
    # options.add_argument('--disable-dev-shm-usage')  # 메모리 제한 비활성화

    # driver = webdriver.Chrome(service=service, options=options)
    # driver.get('https://www.sixshop.com/member/login')

    # username = driver.find_element(By.ID, 'loginEmail')
    # password = driver.find_element(By.ID, 'loginPassword')

    # username.send_keys('innobite')
    # password.send_keys('Dnjswo1613^^')
    # password.send_keys(Keys.RETURN)

    # time.sleep(2)

    # try:
    #   user_element = driver.find_element(By.CLASS_NAME, 'member-name')
    #   return JsonResponse({'status': 'success', 'data': None})
    # except:
    #   return JsonResponse({'status': 'error', 'data': None})


def get_access_cafe24_info(request):
    return JsonResponse({"status": "success", "data": None})
    auth_url = "https://innovape.cafe24api.com/api/v2/oauth/authorize"
    params = {
        "response_type": "code",
        "client_id": config("CAFE24_CLIENT_ID"),
        "state": "innovape",
        "redirect_uri": f"https://super-space-system-rqx764v9wx2w4w-8000.app.github.dev/get-cafe24-auth-code",
        "scope": "mall.read_application",
    }
    url = f"{auth_url}?{urlencode(params)}"
    return redirect(url)


def get_cafe24_auth_code(request):
    code = request.GET.get("code")
    state = request.GET.get("state")

    if code:
        access_token = get_access_token(code)
        return JsonResponse({"access_token": access_token})
    else:
        return JsonResponse({"error": "Authorization code not provided"}, status=400)


def get_access_token(code):
    client_id = config("CAFE24_CLIENT_ID")
    client_secret = config("CAFE24_CLIENT_SECRET_KEY")
    redirect_uri = f"https://super-space-system-rqx764v9wx2w4w-8000.app.github.dev/get-cafe24-auth-code"

    url = "https://innovape.cafe24api.com/api/v2/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        return response.json()  # JSON 응답을 반환
    else:
        # 오류 처리 추가
        return {"error": response.text, "status_code": response.status_code}