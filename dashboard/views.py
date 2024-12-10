import base64
import requests
import pprint
import json
import re
import os
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Category, Product, ProductOptions, Consumer
from django.http import JsonResponse
from bs4 import BeautifulSoup
from django.utils import timezone
from django.db.models import Q
from django.db.models import F
from django.db.models import Func
from django.db import models
from django.core.files.base import ContentFile
from datetime import datetime, timedelta, date
from account.models import Member
from io import BytesIO
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import http.client
from innovape.views import get_access_naver_info, get_access_cafe24_info, get_access_interpark_info, get_access_sixshop_info, get_access_coupang_info, smartstore_product_upload
import time
from .coupang import coupang_product_upload
from .esm_plus import esm_plus_product_upload, esm_plus_product_upload_excel
import zipfile
import io
from django.http import HttpResponse
import shutil


# Create your views here.
class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"  # 사용할 템플릿 파일 지정
    login_url = reverse_lazy("account_login")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop_status = {
            'naver': get_access_naver_info(),
            'interpark': get_access_interpark_info(),
            'coupang': get_access_coupang_info(),
            'sixshop': get_access_sixshop_info(),
            'cafe24': get_access_cafe24_info()
        }
        
        context = {
            'shop_status': shop_status
        }
        
        return context


class DashboardOrderHome(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/order/order_home.html"
    login_url = reverse_lazy("account_login")


class DashboardProductHome(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/product/product_home.html"
    login_url = reverse_lazy("account_login")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        products = Product.objects.all()

        # API 엔드포인트
        url = f"https://sa2.esmplus.com/item/v1/categories/sd-cats/0"
        
        # API 호출에 필요한 헤더
        # headers = {
        #     "Authorization": f"Bearer {settings.GMARKET_API_TOKEN}",
        #     "Accept": "application/json",
        #     "Content-Type": "application/json"
        # }
        
        # API 요청
        response = requests.get(url)
        pprint.pprint(response.json())

        
        context["uploaded_products"] = products.count()
        
        return context
    
    def post(self, request, *args, **kwargs):
        if request.FILES.get('product'):
            print("상품 업로드 시작")
            product_file = request.FILES['product']
            
            try:
                product_df = pd.read_csv(product_file)
                total_rows = len(product_df)
                
                for index, row in product_df.iterrows():
                    print(f"처리 중: {index + 1}/{total_rows} ({((index + 1)/total_rows * 100):.1f}%)")
                    if (pd.notna(row["자체 상품코드"])):
                        try:
                            categories = Category.objects.filter(
                                category_code__in=row["상품분류 번호"].split("|")
                            )
                            details = []
                            origin_details = []
                            origin_thumbnail = ""
                            try:
                                consumer_price = row["소비자가"] if pd.notna(row["소비자가"]) else 0
                                sell_price = row["판매가"] if pd.notna(row["판매가"]) else 0
                                supply_price = row["공급가"] if pd.notna(row["공급가"]) else 0

                                # NaN을 0으로 대체한 후 int로 변환
                                consumer_price = int(consumer_price) if pd.notna(consumer_price) else 0
                                sell_price = int(sell_price) if pd.notna(sell_price) else 0
                                supply_price = int(supply_price) if pd.notna(supply_price) else 0
                                
                            except Exception as e:
                                # NaN을 처리할 수 없을 때 해당 행의 정보를 로깅
                                print(f"Error converting row {index}: {row}")
                                print(f"Error details: {e}")
                                continue

                            # 썸네일 추출
                            thumbnail_src = (
                                "https://ecimg.cafe24img.com/pg1094b33231538027/innovape/web/product/big/"
                                + row["이미지등록(상세)"]
                            )

                            origin_thumbnail = thumbnail_src

                            try:
                                headers = {
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                                    "Referer": "https://ecimg.cafe24img.com/",  # 요청을 보낸 페이지의 URL로 설정
                                }
                                time.sleep(1)  # 2초로 증가
                                response = requests.get(thumbnail_src, headers=headers)
                                response.raise_for_status()  # 요청 실패 시 예외 발생

                                if response.status_code == 200:
                                    print("Image fetched successfully!")
                                    # 이미지 데이터를 바이너리 형식으로 가져옴
                                    image_data = response.content
                                    # 파일 확장자 추출 (URL에서 확장자 추출)
                                    _, extension = os.path.splitext(thumbnail_src)
                                    image_name = f"{int(row['자체 상품코드'])}{extension}"

                                    # ContentFile을 사용하여 Django의 BinaryField에 맞는 형식으로 변환
                                    image_file = ContentFile(image_data)
                                    print("Image data is now ready for use.")
                                else:
                                    print(
                                        f"Failed to fetch image, status code: {response.status_code}"
                                    )
                            except requests.RequestException as e:
                                print(f"Error fetching image from {thumbnail_src}: {e}")
                                
                            # 상세페이지 초기화 작업
                            product_detail_images_path = os.path.join(settings.MEDIA_ROOT, 'product_detail_images')
                            product_code_str = str(int(row['자체 상품코드']))
                            
                            if not os.path.exists(product_detail_images_path):
                                os.makedirs(product_detail_images_path)
                            
                            for filename in os.listdir(product_detail_images_path):
                                if product_code_str in filename:  # 파일 이름에 해당 상품 코드가 포함된 경우
                                    file_path = os.path.join(product_detail_images_path, filename)
                                    if os.path.exists(file_path):
                                        os.remove(file_path)  # 파일 삭제

                            # 상세페이지 추출
                            # BeautifulSoup을 사용하여 HTML에서 img 태그의 src 속성 추출
                            soup = BeautifulSoup(row["상품 상세설명"], "html.parser")
                            img_tags = soup.find_all("img")

                            for index, img_tag in enumerate(img_tags):
                                src = img_tag.get("src")
                                if not src:
                                    continue
                                formatted_src = src.replace("//innovape.cafe24.com/", "")

                                # base_url과 결합하여 절대 URL 생성
                                full_url = f"https://ecimg.cafe24img.com/pg1094b33231538027/innovape/{formatted_src}"
                                origin_details.append(full_url)

                                # 이미지를 다운로드
                                try:
                                    headers = {
                                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                                        "Referer": "https://ecimg.cafe24img.com/",  # 요청을 보낸 페이지의 URL로 설정
                                    }
                                    time.sleep(2)  # 3초로 증가
                                    response = requests.get(full_url, headers=headers)
                                    response.raise_for_status()  # 요청 실패 시 예외 발생

                                    # 이미지 데이터를 바이너리 형식으로 가져옴
                                    detail_image_data = response.content
                                    # 파일 확장자 추출 (URL에서 확장자 추출)
                                    _, extension = os.path.splitext(formatted_src)
                                    detail_image_name = f"{int(row['자체 상품코드'])}_{index}{extension}"

                                    # ContentFile을 사용하여 Django의 BinaryField에 맞는 형식으로 변환
                                    detail_image_file = ContentFile(detail_image_data)
                                    
                                    fs = FileSystemStorage(product_detail_images_path)
                                    file = fs.save(detail_image_name, detail_image_file)
                                    file_url = f"product_detail_images/{detail_image_name}"
                                    
                                    details.append(file_url)
                                except requests.RequestException as e:
                                    print(f"Error fetching image from {full_url}: {e}")
                                    time.sleep(1)  # 5초로 증가
                            
                            product_alternative_price = row["판매가 대체문구"] if pd.notna(row["판매가 대체문구"]) else ""
                            product_author = Member.objects.get(id=self.request.user.id)
                            
                            # 옵션 타이틀 추출
                            option_title = row["옵션입력"].split('//')[1].split('{')[0]
                            
                            # 기기 상품명 다듬기
                            product_name = str(row["상품명"])
                            if "입호흡 전자담배 기기" in product_name:
                                product_name = product_name.replace(" 입호흡 전자담배 기기", "")
                            elif "입호흡 폐호흡 전자담배 기기" in product_name:
                                product_name = product_name.replace(" 입호흡 폐호흡 전자담배 기기", "")
                                
                            # 액상 상품명 다듬기
                            if "52" in row["상품분류 번호"].split("|"):
                                if "입호흡 액상" not in product_name:
                                    product_name += " 입호흡 액상"

                            if "45" in row["상품분류 번호"].split("|"):
                                if "폐호흡 액상" not in product_name:
                                    product_name += " 폐호흡 액상"

                            new_product, created = Product.objects.update_or_create(
                                product_code=str(int(row["자체 상품코드"])),
                                defaults={
                                    "product_cafe24_code": str(row["상품코드"]),
                                    "product_name": product_name,
                                    "product_manage_name": product_name,
                                    "product_description": str(row["상품 요약설명"]),
                                    "product_detail": details,
                                    "product_origin_detail": origin_details,
                                    "product_origin_thumbnail_image": origin_thumbnail,
                                    "product_option": str(row["옵션입력"]),
                                    "product_keywords": str(row["검색어설정"]),
                                    "product_consumer_price": consumer_price,
                                    "product_sell_price": sell_price,
                                    "product_supply_price": supply_price,
                                    "product_alternative_price": product_alternative_price,
                                    "product_seo_title": str(row["검색엔진최적화(SEO) Title"]),
                                    "product_seo_author": str(row["검색엔진최적화(SEO) Author"]),
                                    "product_seo_description": str(row["검색엔진최적화(SEO) Description"]),
                                    "product_seo_keywords": str(row["검색엔진최적화(SEO) Keywords"]),
                                    "product_author": product_author,
                                    "product_created_datetime": datetime.strptime(row["상품등록일"], "%Y-%m-%d"),
                                    "product_modified_datetime": datetime.strptime(row["최근수정일"], "%Y-%m-%d"),
                                },
                            )
                            
                            if new_product.product_thumbnail_image:
                                new_product.product_thumbnail_image.delete(save=False)

                            new_product.product_category.set(categories)
                            new_product.product_thumbnail_image.save(image_name, image_file)

                            new_product.save()
                            print(f"상품 {row['자체 상품코드']} 처리 완료")
                        except Exception as e:
                            print(f"상품 {row['자체 상품코드']} 처리 중 오류 발생: {e}")
                            continue
                        
                return JsonResponse({'status': 'success'})
            except Exception as e:
                print(f"전체 처리 중 오류 발생: {e}")
                return JsonResponse({'status': 'error', 'message': str(e)})
                
        elif request.FILES.get('product_option'):
            print("상품 옵션 업로드 시작")
            product_option_file = request.FILES['product_option']
            try:
                product_option_df = pd.read_csv(product_option_file)
                product_option_counts = {}
                
                for _, row in product_option_df.iterrows():
                    product = Product.objects.get(product_cafe24_code=str(row["상품코드"]))
                    
                    if product.product_code not in product_option_counts:
                        product_option_counts[product.product_code] = 0
                    option_index = product_option_counts[product.product_code]
                    product_option_counts[product.product_code] += 1
                    
                    option_title = product.product_option.split('//')[1].split('{')[0]
                    option_name = str(row["품목명"]).split('/')[1] if '/' in str(row["품목명"]) else str(row["품목명"])
                    
                    # 재고 수량 로직
                    item_name = str(row["품목명"])
                    if "순차 출고" in item_name or "순차출고" in item_name:
                        stock_quantity = 9999
                    else:
                        try:
                            quantity = int(str(row["재고수량"])) if str(row["재고수량"]).isdigit() else 0
                            stock_quantity = quantity if quantity > 0 else 0
                        except ValueError:
                            stock_quantity = 0
                    
                    # 가격 로직 수정
                    try:
                        price_str = str(row["옵션 추가금액"]).replace(',', '')
                        price_float = float(price_str)
                        option_price = int(price_float)
                    except (ValueError, TypeError):
                        option_price = 0
                    
                    new_option, created = ProductOptions.objects.update_or_create(
                        product_option_cafe24_code=str(row["품목코드"]),
                        defaults={
                            'product': product,
                            'product_option_code': product.product_code + str(option_index).zfill(4),
                            'product_option_title': option_title,
                            'product_option_name': option_name,
                            'product_option_display_name': str(row["품목명"]),
                            'product_option_stock': stock_quantity,
                            'product_option_price': option_price,
                        },
                    )

                return JsonResponse({'status': 'success'})
            except Exception as e:
                print(f"Error is : {e}")
                return JsonResponse({'status': 'error', 'message': str(e)})


class DashboardProductAdd(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/product/product_add.html"
    login_url = reverse_lazy("account_login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        categories = Category.objects.all()
        products = Product.objects.all()

        context["categories"] = categories
        context["products"] = products

        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get("code") == "parse_html":
            html_content = request.POST.get("html_content")
            urls = []
            options = []
            thumbnail_binary_data = b""
            supply_price_text = 0

            # HTML 유효성 검사
            if not self.is_valid_html(html_content):
                return JsonResponse(
                    {"status": "error", "message": "유효하지 않은 HTML 형식입니다."},
                    status=400,
                )

            # HTML이 유효한 경우 처리
            soup = BeautifulSoup(html_content, "html.parser")

            if request.POST.get("mall") == "메두사":
                # CSS 선택자를 사용하여 img 태그 선택
                base_url = "https://medusamall.com"
                img_tags = soup.select("#prdDetail > div.cont img")
                thumbnail_img_tag = soup.select_one("#big_img_box > div > img")
                supply_price_tag = soup.select_one("#span_product_price_text")
                option_tags = soup.select("#product_option_id1 > optgroup > option")

                if not option_tags:
                    option_tags = soup.select("#product_option_id1 > option")

                # 공급가 크롤링
                if supply_price_tag:
                    supply_price_text = supply_price_tag.get_text(strip=True)

                    if len(supply_price_text) > 0:
                        supply_price_text = supply_price_text.replace(",", "")
                        supply_price_text = supply_price_text[:-1]

                # 옵션 크롤링
                if option_tags:
                    for option in option_tags:
                        opt = option.get_text(strip=True)
                        if opt:
                            options.append(opt)

                # 썸네일 크롤링
                thumbnail_src = thumbnail_img_tag.get("src")
                if thumbnail_src:
                    if thumbnail_src.startswith("data:image/"):  # Base64 이미지 처리
                        # Base64 데이터에서 MIME 타입과 데이터를 분리
                        header, encoded = thumbnail_src.split(",", 1)
                        thumbnail_binary_data = base64.b64decode(encoded)
                    else:  # URL 방식의 이미지 처리
                        # URL이 상대 경로인 경우 절대 경로로 변환
                        if not thumbnail_src.startswith(
                            "http://"
                        ) and not thumbnail_src.startswith("https://"):
                            thumbnail_src = "https:" + thumbnail_src

                        try:
                            headers = {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                                "Referer": "https://medusamall.com/",  # 요청을 보낸 페이지의 URL로 설정
                            }
                            response = requests.get(thumbnail_src, headers=headers)
                            response.raise_for_status()  # 요청 실패 시 예외 발생
                            base64_encoded_data = base64.b64encode(
                                response.content
                            ).decode("utf-8")
                            json_data = json.dumps({"image_data": base64_encoded_data})
                            loaded_data = json.loads(json_data)
                            thumbnail_binary_data = loaded_data["image_data"]
                        except requests.RequestException as e:
                            print(f"Error fetching image from {thumbnail_src}: {e}")

                # 상세페이지 크롤링
                for img in img_tags:
                    src = img.get("src")
                    if src:
                        if src.startswith("data:image/"):  # Base64 이미지 처리
                            # Base64 데이터에서 MIME 타입과 데이터를 분리
                            header, encoded = src.split(",", 1)
                            binary_data = base64.b64decode(encoded)
                        else:  # URL 방식의 이미지 처리
                            # URL이 상대 경로인 경우 절대 경로로 변환
                            if not src.startswith("http://") and not src.startswith(
                                "https://"
                            ):
                                src = base_url + src.replace("//", "/")

                            try:
                                headers = {
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                                    "Referer": "https://medusamall.com/",  # 요청을 보낸 페이지의 URL로 설정
                                }
                                response = requests.get(src, headers=headers)
                                response.raise_for_status()  # 요청 실패 시 예외 발생
                                binary_data = response.content
                                base64_encoded_data = base64.b64encode(binary_data).decode("utf-8")
                                urls.append(f"data:image/jpeg;base64,{base64_encoded_data}")
                            except requests.RequestException as e:
                                print(f"Error fetching image from {src}: {e}")
                                continue  # 오류가 발생한 경우 다음 이미지로 넘어감

            return JsonResponse(
                {
                    "status": "success",
                    "data": {
                        "detail_urls": urls,
                        "thumbnail_binary_data": thumbnail_binary_data,
                        "supply_price": supply_price_text,
                        "options": options,
                    },
                }
            )

        elif request.POST.get("code") == "product_add":
            data = json.loads(request.POST.get("data"))

            # 제품 코드 생성
            product_cafe24_code = self.generate_product_code()

            # 카테고리, 디스플레이, 옵션 제품, 관련 제품을 한 번에 조회
            categories = Category.objects.filter(id__in=data["product_category"])
            related_products = Product.objects.filter(
                product_name__in=data["product_related_products"]
            )
            
            # 썸네일 업로드
            thumbnail_extension = data["product_thumbnail_image"].split(';')[0].split('/')[1]
            thumbnail_image_name = f"{data['product_code']}.{thumbnail_extension}"
            thumbnail_image_file = ContentFile(
                base64.b64decode(data["product_thumbnail_image"].split(',')[1]),
                name=thumbnail_image_name
            )
            
            # 상세페이지 업로드
            product_detail_images_path = os.path.join(settings.MEDIA_ROOT, 'product_detail_images')
            details = []

            if not os.path.exists(product_detail_images_path):
                os.makedirs(product_detail_images_path)
                
            for filename in os.listdir(product_detail_images_path):
                if str(data['product_code']) in filename:  # 파일 이름에 해당 상품 코드가 포함된 경우
                    file_path = os.path.join(product_detail_images_path, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)  # 파일 삭제
                
            for index, detail_url in enumerate(data["product_detail"]):
                detail_extension =detail_url.split(';')[0].split('/')[1]
                detail_image_name = f"{data['product_code']}_{index}.{detail_extension}"
                detail_image_file = ContentFile(
                    base64.b64decode(detail_url.split(',')[1]),
                    name=detail_image_name
                )

                fs = FileSystemStorage(product_detail_images_path)
                file = fs.save(detail_image_name, detail_image_file)
                file_url = f"product_detail_images/{detail_image_name}"

                details.append(file_url)
            # 제품 업데이트 또는 생성
            new_product, created = Product.objects.update_or_create(
                product_code=data["product_code"],
                defaults={
                    'product_cafe24_code': product_cafe24_code,
                    "product_name": data["product_name"],
                    "product_manage_name": data["product_manage_name"],
                    "product_description": data["product_description"],
                    "product_detail": details,
                    "product_keywords": data["product_keywords"],
                    "product_consumer_price": int(data["product_customer_price"]),
                    "product_sell_price": int(data["product_sell_price"]),
                    "product_supply_price": int(data["product_supply_price"]),
                    "product_alternative_price": data["product_alternative_price"],
                    "product_seo_title": data["product_seo_title"],
                    "product_seo_author": data["product_seo_author"],
                    "product_seo_description": data["product_seo_description"],
                    "product_seo_keywords": data["product_seo_keywords"],
                    "product_author": request.user,
                    "product_created_datetime": timezone.now(),
                },
            )
            # 상품코드,자체상품코드,품목명,재고수량,옵션추가금액

            # 관계 설정 (중간 리스트 없이 바로 set() 호출)
            new_product.product_category.set(categories)
            new_product.product_related_products.set(related_products)
            
            if new_product.product_thumbnail_image:
                new_product.product_thumbnail_image.delete(save=False)
            new_product.product_thumbnail_image.save(thumbnail_image_name, thumbnail_image_file)

            # 제품 저장
            new_product.save()

            return JsonResponse({"status": "success"})
        elif request.POST.get("code") == "product_options_add":
            data = json.loads(request.POST.get("data"))
            product = Product.objects.get(product_code=data["product_code"])

            for index, option in enumerate(data["options_data"]):
                new_option, created = ProductOptions.objects.update_or_create(
                    product_option_code=product.product_code + str(index).zfill(4),
                    defaults={
                        'product': product,
                        'product_option_title': data["product_option_title"],
                        'product_option_name': option["product_option_name"],
                        'product_option_display_name': option["product_option_display_name"],
                        'product_option_stock': int(option["product_option_stock"]),
                        'product_option_price': int(option["product_option_price"]),
                    },
                )

            return JsonResponse({"status": "success"})

    def is_valid_html(self, html):
        try:
            # BeautifulSoup을 사용하여 HTML 파싱
            soup = BeautifulSoup(html, "html.parser")
            return bool(soup.find())  # 유효한 HTML이면 True 반환
        except Exception:
            return False  # 예외가 발생하면 유효하지 않음

    def generate_product_code(self):
        prefix = "P"  # 상품 코드 앞부분 (P)
        num_digits = 6  # 숫자 부분의 자리수 (6자리)
        letter_max = 26  # 알파벳 A-Z (26글자)

        # 마지막 상품 코드 가져오기
        last_product = Product.objects.all().order_by("-product_cafe24_code").first()

        if last_product:
            last_code = last_product.product_cafe24_code

            # 'P'로 시작하는지 확인
            if not last_code.startswith("P"):
                raise ValueError("코드는 'P'로 시작해야 합니다.")

            # 숫자 부분과 알파벳 부분 분리
            num_part = re.search(r"\d+", last_code[1:]).group()  # 숫자 부분
            letter_part = re.sub(r"\d", "", last_code[1:])  # 알파벳 부분

            # 알파벳 부분이 전부 'Z'인 경우 처리
            if letter_part == "Z" * len(letter_part):
                # 알파벳 부분이 모두 'Z'일 경우
                new_num_length = len(num_part) - 1  # 숫자 자릿수는 1자리 줄어듬
                new_letter_length = len(letter_part) + 1  # 알파벳 자리는 1자리 늘어남

                # 숫자는 자릿수를 줄여서 0으로 채운다
                next_num_part = "0" * new_num_length
                # 알파벳 부분은 길이를 늘려서 'A'로 채운다
                next_letter_part = "A" * new_letter_length

            else:
                # 알파벳 부분에서 끝이 'Z'일 경우, 끝부터 차례대로 변경
                next_letter_part = list(letter_part)  # 알파벳을 리스트로 다룬다
                for i in range(len(next_letter_part) - 1, -1, -1):
                    if next_letter_part[i] == "Z":
                        next_letter_part[i] = "A"  # Z는 A로 변경
                    else:
                        next_letter_part[i] = chr(
                            ord(next_letter_part[i]) + 1
                        )  # Z가 아니면 1 증가
                        break
                next_letter_part = "".join(next_letter_part)  # 다시 문자열로 합침

                # 숫자 부분 1 증가
                next_num_part = str(int(num_part)).zfill(
                    len(num_part)
                )  # 자리수 맞추기 위해 zfill 사용

            # 최종적으로 'P' + 숫자 부분 + 알파벳 부분을 반환
            print(next_num_part, next_letter_part)
            return "P" + next_num_part + next_letter_part


class DashboardProductList(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/product/product_list.html"
    login_url = reverse_lazy("account_login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 카테고리 데이터를 가져옵니다.
        categories = Category.objects.all()
        context["categories"] = categories

        return context

    def get_filtered_products(self, search_field, search_title, search_category, start_date, end_date, start, length):
        # 기본 쿼리셋
        queryset = Product.objects.all().order_by('-product_code')

        # 검색 필드 및 제목에 따른 필터링
        if search_field:
            if search_title == 'name':
                queryset = queryset.filter(product_name__icontains=search_field)
            elif search_title == 'manage_name':
                queryset = queryset.filter(product_manage_name__icontains=search_field)
            elif search_title == 'cafe24_code':
                queryset = queryset.filter(product_cafe24_code__icontains=search_field)
            elif search_title == 'smartstore_code':
                queryset = queryset.filter(product_smartstore_code__icontains=search_field)
            elif search_title == 'smartstore_channel_code':
                queryset = queryset.filter(product_smartstore_channel_code__icontains=search_field)
            elif search_title == 'coupang_code':
                queryset = queryset.filter(product_coupang_code__icontains=search_field)
            elif search_title == 'code':
                queryset = queryset.filter(product_code__icontains=search_field)
            elif search_title == 'author':
                queryset = queryset.filter(product_author__username__icontains=search_field)

        # 카테고리 필터링
        if search_category:
            queryset = queryset.filter(product_category__id__in=search_category)

        # 날짜 범위 필터링
        if start_date and end_date:
            date_field = 'product_created_datetime'  # 기본값은 생성일
            if self.request.GET.get('search_date_title') == 'modified':
                date_field = 'product_modified_datetime'
            
            # 날짜 범위에 end_date도 포함되도록 하루를 더함
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            date_filter = {
                f'{date_field}__range': [start_date, end_date]
            }
            queryset = queryset.filter(**date_filter)

        return queryset[start:start+length]

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            # GET 요청으로 필터링 조건을 받아옵니다.
            search_field = self.request.GET.get("search_field", "")
            search_title = self.request.GET.get("search_title", "name")
            search_category = self.request.GET.getlist("search_category", [])
            start_date = self.request.GET.get("start_date", "")
            end_date = self.request.GET.get("end_date", "")
        
            # 페이지네이션을 위한 start와 length 파라미터 추가
            start = int(self.request.GET.get("start", 0))
            length = int(self.request.GET.get("length", 10))
            
            # 전체 데이터셋 크기
            total_records = Product.objects.count()

            # 필터링된 제품을 가져옵니다.
            filtered_queryset = self.get_filtered_products(
                search_field, search_title, search_category, start_date, end_date, 0, total_records
            )
            filtered_count = filtered_queryset.count()

            # 페이지네이션 적용된 제품
            paginated_queryset = filtered_queryset[start:start + length]

            # 각 제품에 대한 카테고리와 디스플레이 값 처리
            data = []
            for product in paginated_queryset:
                categories = '<br>'.join([
                    (f"{category.category_parent.category_name} > {category.category_name}" 
                    if category.category_parent else category.category_name) 
                    for category in product.product_category.all()
                ])
                data.append({
                    'product_thumbnail_image': product.product_thumbnail_image.url if product.product_thumbnail_image else None,
                    'product_code': product.product_code,
                    'product_name': product.product_name,
                    'product_categories': categories,
                    'product_consumer_price': product.product_consumer_price,
                    'product_sell_price': product.product_sell_price,
                    'product_supply_price': product.product_supply_price,
                    'product_author': product.product_author.username,
                    'product_created_datetime': product.product_created_datetime,
                    'product_modified_datetime': product.product_modified_datetime,
                })

            return JsonResponse(
                {
                    "draw": int(self.request.GET.get("draw", 0)),
                    "recordsTotal": total_records,
                    "recordsFiltered": filtered_count,
                    "data": data,
                }
            )

        return super().render_to_response(context, **response_kwargs)
    
    def post(self, request, *args, **kwargs):
        if request.POST.get("code") == "product_upload":
            products = Product.objects.all()
            
            # 스마트스토어 상품 업로드
            for product in products:
                # 특정 카테고리에 속한 상품만 업로드
                UPLOAD_CATEGORY_CODES = ['43', '51', '124', '137', '138', '125']
                if (product.product_category.filter(category_code__in=UPLOAD_CATEGORY_CODES).exists() and 
                    not product.product_smartstore_is_prohibitted):
                    try:
                        smartstore_product_upload(product.product_code, product.product_smartstore_code)
                    except Exception as e:
                        print(f"Error uploading product {product.product_code}: {str(e)}")
                    
            return JsonResponse({"status": "success"})
        elif request.POST.get("code") == "product_smartstore_first_upload":
            products = Product.objects.filter(
                Q(product_smartstore_code__isnull=True) | Q(product_smartstore_code=''),
                product_smartstore_is_prohibitted=False
            )
            
            # 스마트스토어 상품 업로드
            for product in products:
                # 특정 카테고리에 속한 상품만 업로드
                UPLOAD_CATEGORY_CODES = ['43', '51', '124', '137', '138', '125']
                if product.product_category.filter(category_code__in=UPLOAD_CATEGORY_CODES).exists():
                    try:
                        smartstore_product_upload(product.product_code, product.product_smartstore_code)
                    except Exception as e:
                        print(f"Error uploading product {product.product_code}: {str(e)}")
                    
            return JsonResponse({"status": "success"})
        elif request.POST.get("code") == "product_coupang_first_upload":
            try:
                products = Product.objects.filter(
                    Q(product_coupang_code__isnull=True) | Q(product_coupang_code=''),
                    product_coupang_is_prohibitted=False
                ).values_list('product_code', flat=True)
                
                # 엑셀 파일 생성
                excel_filename = coupang_product_upload(products)
                
                if excel_filename:
                    # ZIP 파일 생성을 위한 메모리 버퍼
                    zip_buffer = io.BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        # 엑셀 파일 추가
                        excel_path = os.path.join(settings.MEDIA_ROOT, 'upload_forms', excel_filename)
                        zip_file.write(excel_path, excel_filename)
                        
                        # 선택된 상품들의 이미지 파일 추가
                        for product_code in products:
                            product = Product.objects.get(product_code=product_code)
                            
                            # 썸네일 이미지 추가
                            if product.product_thumbnail_image:
                                thumb_path = os.path.join(settings.MEDIA_ROOT, str(product.product_thumbnail_image))
                                if os.path.exists(thumb_path):
                                    # 임시 파일로 복사하면서 원본 속성 유지
                                    temp_thumb = os.path.join(settings.MEDIA_ROOT, 'temp', os.path.basename(thumb_path))
                                    os.makedirs(os.path.dirname(temp_thumb), exist_ok=True)
                                    shutil.copy2(thumb_path, temp_thumb)  # copy2는 메타데이터를 포함한 복사
                                    zip_file.write(temp_thumb, f'images/thumbnails/{os.path.basename(thumb_path)}')
                                    os.remove(temp_thumb)  # 임시 파일 삭제
                                
                            # 상세 이미지들 추가
                            for detail_image in product.product_detail:
                                detail_path = os.path.join(settings.MEDIA_ROOT, detail_image)
                                if os.path.exists(detail_path):
                                    # 임시 파일로 복사하면서 원본 속성 유지
                                    temp_detail = os.path.join(settings.MEDIA_ROOT, 'temp', os.path.basename(detail_path))
                                    os.makedirs(os.path.dirname(temp_detail), exist_ok=True)
                                    shutil.copy2(detail_path, temp_detail)
                                    zip_file.write(temp_detail, f'images/details/{os.path.basename(detail_path)}')
                                    os.remove(temp_detail)  # 임시 파일 삭제
                    
                    # ZIP 파일 응답 생성
                    zip_buffer.seek(0)
                    timestamp = time.strftime('%Y%m%d_%H%M%S')
                    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="coupang_upload_package_{timestamp}.zip"'
                    
                    return response
                else:
                    return JsonResponse({'status': 'error', 'message': '파일 생성 실패'})
                    
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        elif request.POST.get("code") == "product_esm_plus_first_upload":
            try:
                products = Product.objects.filter(
                    Q(product_esm_plus_code__isnull=True) | Q(product_esm_plus_code=''),
                    product_esm_plus_is_prohibitted=False
                ).values_list('product_code', flat=True)
                
                # 엑셀 파일 생성
                result_files = esm_plus_product_upload_excel(products)
                
                # 생성된 파일들의 URL 목록 반환
                file_urls = []
                for file_path in result_files:
                    # MEDIA_ROOT 경로를 MEDIA_URL로 변환
                    relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
                    file_url = os.path.join(settings.MEDIA_URL, relative_path)
                    file_urls.append(file_url)

                return JsonResponse({
                    'status': 'success',
                    'files': file_urls
                })
                
            except Exception as e:
                return JsonResponse({
                    'status': 'error', 
                    'message': str(e)
                })


class DashboardProductCategory(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/product/product_add.html"
    login_url = reverse_lazy("account_login")


class DashboardProductDisplay(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/product/product_add.html"
    login_url = reverse_lazy("account_login")


class DashboardProductInventory(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/product/product_add.html"
    login_url = reverse_lazy("account_login")


class DashboardProductOutofstock(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/product/product_add.html"
    login_url = reverse_lazy("account_login")


class DashboardConsumerHome(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/consumer/consumer_home.html"
    login_url = reverse_lazy("account_login")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        new_consumers = Consumer.objects.filter(
            consumer_register_dt__gte=(date.today() - timedelta(days=7)),
            consumer_register_dt__lte=date.today()
        )
        not_verified_consumers = Consumer.objects.filter(consumer_verify_dt=None)
        all_consumers = Consumer.objects.all()
        
        context["new_consumers"] = new_consumers.count()
        context["not_verified_consumers"] = not_verified_consumers.count()
        context["all_consumers"] = all_consumers.count()
        
        return context
    
    def post(self, request, *args, **kwargs):
        if request.FILES.get('consumer'):
            consumer_file = request.FILES['consumer']
            
            try:
                consumer_df = pd.read_csv(consumer_file)
                
                for index, row in consumer_df.iterrows():
                    self.upload_cafe24_consumer_excel(row)
                
                return JsonResponse({'status': 'success'})
            except Exception as e:
                print(e)

    def upload_cafe24_consumer_excel(self, row):
        try:
            new_consumer, created = Consumer.objects.update_or_create(
                consumer_id=str(row["아이디"]),
                defaults={
                    "consumer_grade": str(row["회원등급"]),
                    "consumer_name": str(row["이름"]),
                    "consumer_phone_number": str(row["휴대폰번호"]),
                    "consumer_email": str(row["이메일"]),
                    "consumer_birth": datetime.strptime(str(row["생년월일"]), '%Y-%m-%d'),
                    "consumer_area": str(row["지역"]),
                    "consumer_base_address": str(row["주소1"]),
                    "consumer_detail_address": str(row["주소2"]),
                    "consumer_refund_account": str(row["환불계좌정보(은행/계좌/예금주)"]) if str(row["환불계좌정보(은행/계좌/예금주)"]) and str(row["환불계좌정보(은행/계좌/예금주)"]).lower() != "nan" else '',
                    "consumer_total_visits": int(row["총 방문횟수(1년 내)"]),
                    "consumer_total_orders": int(row["총 실주문건수"]),
                    "consumer_total_purchase": int(row["총구매금액"]),
                    "consumer_last_order_dt": datetime.strptime(str(row["최종주문일"]), "%Y-%m-%d %H:%M:%S") if str(row["최종주문일"]) and str(row["최종주문일"]).lower() != "nan" else None,
                    "consumer_last_connection_dt": datetime.strptime(str(row["최종접속일"]), "%Y-%m-%d %H:%M:%S") if str(row["최종접속일"]) and str(row["최종접속일"]).lower() != "nan" else None,
                    "consumer_register_dt": datetime.strptime(str(row["회원 가입일"]), "%Y-%m-%d"),
                    "consumer_register_path": str(row["회원 가입경로"]),
                },
            )
            new_consumer.save()
            print("Consumer updated or created successfully.")
            
            return JsonResponse({'status', 'success'})

        except Exception as e:
            print(f"Error occurred: {e}")