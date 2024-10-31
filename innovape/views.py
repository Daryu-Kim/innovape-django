from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from decouple import config
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import bcrypt
import pybase64
import requests

def login_check_view(request):
  if request.user.is_authenticated:
    return redirect('/dashboard/home')
  else:
    return redirect('/account/login')
  
def get_access_naver_info(request):
  client_id = config('NAVER_COMMERCE_ID')
  cilent_secret = config('NAVER_COMMERCE_SECRET')
  timestamp = int(time.time() * 1000)
  print(client_id, cilent_secret, timestamp)
  
  password = client_id + "_" + str(timestamp)
  hashed = bcrypt.hashpw(password.encode('utf-8'), cilent_secret.encode('utf-8'))
  encode_hashed = pybase64.standard_b64encode(hashed).decode('utf-8')
  
  data = {
    'client_id': client_id,
    'timestamp': timestamp,
    'grant_type': 'client_credentials',
    'client_secret_sign': encode_hashed,
    'type': "SELF",
	}
  
  url = 'https://api.commerce.naver.com/external/v1/oauth2/token'
  
  response = requests.post(url, data=data)
  if response.status_code == 200:
    return JsonResponse({'status': 'success', 'data': response.json()})
  else:
    return JsonResponse({'status': 'error', 'data': response.json()})
  
def get_access_coupang_info(request):
  expires = datetime.strptime(config('COUPANG_SECRET_KEY_EXPIRES'), "%Y-%m-%d %H:%M")
  now = datetime.now()
  
  if expires > now:
    difference = expires - now
    days_left = difference.days
    return JsonResponse({'status': 'success', 'data': days_left})
  else:
    return JsonResponse({'status': 'error', 'data': 0})
  
def get_access_interpark_info(request):
  # 인증키 발급 승인 후 개발 필요
  return JsonResponse({'status': 'error', 'data': None})

def get_access_sixshop_info(request):
  service = Service('') # '' 안에 서버에서 사용할 크롬 드라이버 경로를 넣어줘야함.

  options = Options()
  options.add_argument('--headless')  # 헤드리스 모드
  options.add_argument('--no-sandbox')  # 샌드박스 모드 비활성화
  options.add_argument('--disable-dev-shm-usage')  # 메모리 제한 비활성화

  driver = webdriver.Chrome(service=service, options=options)
  driver.get('https://www.sixshop.com/member/login')

  username = driver.find_element(By.ID, 'loginEmail')
  password = driver.find_element(By.ID, 'loginPassword')

  username.send_keys('innobite')
  password.send_keys('Dnjswo1613^^')
  password.send_keys(Keys.RETURN)

  time.sleep(2)

  try:
    user_element = driver.find_element(By.CLASS_NAME, 'member-name')
    return JsonResponse({'status': 'success', 'data': None})
  except:
    return JsonResponse({'status': 'error', 'data': None})
  
def get_access_cafe24_info(request):
  url = "https://innovape.cafe24api.com/api/v2/admin/store?shop_no=1"
  headers = {
      'Authorization': "Bearer {access_token}",
      'Content-Type': "application/json",
      'X-Cafe24-Api-Version': "{version}"
      }
  response = requests.request("GET", url, headers=headers)
  print(response.text)