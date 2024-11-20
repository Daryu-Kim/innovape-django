import base64
import requests
import pprint
import json
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Category, Display, Product
from django.http import JsonResponse
from bs4 import BeautifulSoup

# Create your views here.
class DashboardHomeView(LoginRequiredMixin, TemplateView):
class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'  # 사용할 템플릿 파일 지정
    login_url = reverse_lazy('account_login')

class DashboardOrderHome(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/order/order_home.html'
    login_url = reverse_lazy('account_login')

class DashboardProductHome(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/product/product_home.html'
    login_url = reverse_lazy('account_login')

class DashboardProductAdd(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/product/product_add.html'
    login_url = reverse_lazy('account_login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        categories = Category.objects.all()
        displays = Display.objects.all()
        products = Product.objects.all()

        context['categories'] = categories
        context['displays'] = displays
        context['products'] = products

        return context
    
    def post(self, request, *args, **kwargs):
        if request.POST.get('code') == 'parse_html':
            html_content = request.POST.get('html_content')
            urls = []
            options = []
            thumbnail_binary_data = b''
            supply_price_text = 0
            customer_price_text = 0

            # HTML 유효성 검사
            if not self.is_valid_html(html_content):
                return JsonResponse({'status': 'error', 'message': '유효하지 않은 HTML 형식입니다.'}, status=400)

            # HTML이 유효한 경우 처리
            soup = BeautifulSoup(html_content, 'html.parser')

            if request.POST.get('mall') == "메두사":
                # CSS 선택자를 사용하여 img 태그 선택
                base_url = "https://medusamall.com"
                img_tags = soup.select('#prdDetail > div.cont img')
                thumbnail_img_tag = soup.select_one('#big_img_box > div > img')
                supply_price_tag = soup.select_one('#span_product_price_text')
                customer_price_tag = soup.select_one('#span_product_price_custom')
                option_tags = soup.select('#product_option_id1 > optgroup > option')

                # 공급가 크롤링
                if supply_price_tag:
                    supply_price_text = supply_price_tag.get_text(strip=True)
                    
                    if len(supply_price_text) > 0:
                        supply_price_text = supply_price_text.replace(',', '')
                        supply_price_text = supply_price_text[:-1]

                # 소비자가 크롤링
                if customer_price_tag:
                    customer_price_text = customer_price_tag.get_text(strip=True)
                    
                    if len(customer_price_text) > 0:
                        customer_price_text = customer_price_text.replace(',', '')
                        customer_price_text = customer_price_text[:-1]

                # 옵션 크롤링
                if option_tags:
                    for option in option_tags:
                        opt = option.get_text(strip=True)
                        if opt:
                            options.append(opt)

                # 썸네일 크롤링
                thumbnail_src = thumbnail_img_tag.get('src')
                if thumbnail_src:
                    if thumbnail_src.startswith('data:image/'):  # Base64 이미지 처리
                        # Base64 데이터에서 MIME 타입과 데이터를 분리
                        header, encoded = thumbnail_src.split(',', 1)
                        thumbnail_binary_data = base64.b64decode(encoded)
                    else:  # URL 방식의 이미지 처리
                        # URL이 상대 경로인 경우 절대 경로로 변환
                        if not thumbnail_src.startswith('http://') and not thumbnail_src.startswith('https://'):
                            thumbnail_src = 'https:' + thumbnail_src

                        try:
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                                'Referer': 'https://medusamall.com/'  # 요청을 보낸 페이지의 URL로 설정
                            }
                            response = requests.get(thumbnail_src, headers=headers)
                            response.raise_for_status()  # 요청 실패 시 예외 발생
                            base64_encoded_data = base64.b64encode(response.content).decode('utf-8')
                            json_data = json.dumps({'image_data': base64_encoded_data})
                            loaded_data = json.loads(json_data)
                            thumbnail_binary_data = loaded_data['image_data']
                        except requests.RequestException as e:
                            print(f"Error fetching image from {thumbnail_src}: {e}")

                # 상세페이지 크롤링
                for img in img_tags:
                    src = img.get('src')
                    if src:
                        if src.startswith('data:image/'):  # Base64 이미지 처리
                            # Base64 데이터에서 MIME 타입과 데이터를 분리
                            header, encoded = src.split(',', 1)
                            binary_data = base64.b64decode(encoded)
                        else:  # URL 방식의 이미지 처리
                            # URL이 상대 경로인 경우 절대 경로로 변환
                            if not src.startswith('http://') and not src.startswith('https://'):
                                src = base_url + src.replace('//', '/')

                            try:
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                                    'Referer': 'https://medusamall.com/'  # 요청을 보낸 페이지의 URL로 설정
                                }
                                response = requests.get(src, headers=headers)
                                response.raise_for_status()  # 요청 실패 시 예외 발생
                                binary_data = response.content
                            except requests.RequestException as e:
                                print(f"Error fetching image from {src}: {e}")
                                continue  # 오류가 발생한 경우 다음 이미지로 넘어감
                        
                        # imgbb에 업로드
                        response = self.upload_to_imgbb(binary_data)
                        if response and 'data' in response:
                            urls.append(response['data']['url'])
            
            return JsonResponse({'status': 'success', 'data': {'detail_urls': urls, 'thumbnail_binary_data': thumbnail_binary_data, 'customer_price': customer_price_text, 'supply_price': supply_price_text, 'options': options }})

    def is_valid_html(self, html):
        try:
            # BeautifulSoup을 사용하여 HTML 파싱
            soup = BeautifulSoup(html, 'html.parser')
            return bool(soup.find())  # 유효한 HTML이면 True 반환
        except Exception:
            return False  # 예외가 발생하면 유효하지 않음
        
    def upload_to_imgbb(self, binary_data):
        imgbb_api_key = 'd871f58378653057ddb74a4a23a7e629'  # 여기에 imgbb API 키를 입력하세요.
        url = 'https://api.imgbb.com/1/upload'
        files = {
            'image': binary_data
        }
        params = {
            'key': imgbb_api_key
        }

        response = requests.post(url, params=params, files=files)
        pprint.pprint(response)
        if response.status_code == 200:
            return response.json()
        return None

class DashboardProductList(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/product/product_add.html'
    login_url = reverse_lazy('account_login')

class DashboardProductCategory(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/product/product_add.html'
    login_url = reverse_lazy('account_login')

class DashboardProductDisplay(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/product/product_add.html'
    login_url = reverse_lazy('account_login')

class DashboardProductInventory(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/product/product_add.html'
    login_url = reverse_lazy('account_login')

class DashboardProductOutofstock(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/product/product_add.html'
    login_url = reverse_lazy('account_login')