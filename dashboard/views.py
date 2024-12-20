import base64
import requests
import pprint
import json
import re
import os
import math
from collections import defaultdict
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Category, Product, ProductOptions, Consumer, CartItem, Order
from .order import generate_manual_order_number, generate_manual_order_product_number
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
from innovape.views import get_access_naver_info, get_access_cafe24_info, get_access_interpark_info, get_access_sixshop_info, get_access_coupang_info
import time
from .coupang import coupang_product_upload
from .esm_plus import esm_plus_product_upload_excel
from .cafe24 import cafe24_product_upload, cafe24_option_upload
import zipfile
import io
from django.http import HttpResponse
import shutil
import traceback
from django.core.cache import cache
from .order import generate_order_number
from .crawl_utils import medusa_crawl, siasiucp_crawl, check_origin_base_url, convert_image

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        deposit_waiting = Order.objects.filter(order_status="입금대기").count()
        order_waiting = Order.objects.filter(order_status="상품발주대기").count()
        package_waiting = Order.objects.filter(order_status="상품포장중").count()
        cancel_request = Order.objects.filter(order_status="취소요청").count()
        refund_request = Order.objects.filter(order_status="환불요청").count()
        exchange_request = Order.objects.filter(order_status="교환요청").count()
        
        context["deposit_waiting"] = deposit_waiting
        context["order_waiting"] = order_waiting
        context["package_waiting"] = package_waiting
        context["cancel_request"] = cancel_request
        context["refund_request"] = refund_request
        context["exchange_request"] = exchange_request

        return context
    
class DashboardShopHome(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/shop/shop_home.html"
    login_url = reverse_lazy("account_login")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        CATEGORY_LIST = ["입호흡 기기", "폐호흡 기기", "일회용 기기", "입호흡 액상", "폐호흡 액상"]

        # 제외할 문자열 목록
        excluded_strings = ["빠른출고", "빠른 출고"]

        # Q 객체를 사용하여 exclude 조건을 설정
        query = Q()
        for string in excluded_strings:
            query |= Q(product_option_display_name__icontains=string)
            
        cache.clear()

        # 카테고리 캐시
        parent_categories = cache.get('parent_categories')
        if not parent_categories:
            parent_categories = Category.objects.filter(category_parent__isnull=True).exclude(category_name__in=["EVENT!", "인기 브랜드관"])
            cache.set('parent_categories', parent_categories, timeout=900)  # 15분 동안 캐시

        context["categories"] = parent_categories

        return context
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        if data.get('code') == "load_tab_products":
            category_id = data.get('category_id')
            page = int(data.get('page', 1))
            page_size = 12
            start = (page - 1) * page_size
            end = start + page_size
            
            # 제외할 문자열 목록
            excluded_strings = ["빠른출고", "빠른 출고"]

            # Q 객체를 사용하여 exclude 조건을 설정
            query = Q()
            for string in excluded_strings:
                query |= Q(product_option_display_name__icontains=string)

            if category_id == "recommend":
                products = Product.objects.filter(product_is_recommend=True)[start:end]
            elif category_id == "new":
                products = Product.objects.filter(product_is_new=True)[start:end]
            else:
                products = Product.objects.filter(product_category__id=category_id)[start:end]
                
            product_options = ProductOptions.objects.filter(product__in=products)
            product_list = []
            options_list = []
            
            is_last_page = len(products) < page_size
            
            for product in products:
                options = product_options.filter(product=product).filter(query)
                
                for option in options:
                    options_list.append({
                        'product_option_code': option.product_option_code,
                        'product_option_name': option.product_option_name,
                        'product_option_price': option.product_option_price,
                        'product_code': product.product_code,
                    })
                product_list.append({
                    'product_code': product.product_code,
                    'product_name': product.product_name,
                    'product_thumbnail_image': product.product_thumbnail_image.url,
                    'product_sell_price': product.product_sell_price,
                    'product_manager_price': product.product_manager_price,
                    'product_description': product.product_description,
                    'product_detail': product.product_detail,
                    'options': options_list
                })   
            
            return JsonResponse({'status': 'success', 'products': product_list, 'is_last_page': is_last_page})
        elif data.get('code') == "add_to_cart":
            try:
                cart_items = data.get('items', [])
                
                for item in cart_items:
                    product = Product.objects.get(product_code=item['product_code'])
                    product_option = ProductOptions.objects.get(product_option_code=item['option_code'])
                    
                    cart_item, created = CartItem.objects.update_or_create(
                        member_id=request.user.username,
                        product_code=product.product_code,
                        product_option_code=product_option.product_option_code,
                        defaults={
                            'quantity': item['quantity']
                        }
                    )
                    
                return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
            
        elif data.get('code') == "get_cart_items":
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(member_id=request.user.username)
                grouped_items = defaultdict(list)

                # 상품을 옵션별로 그룹화
                for item in cart_items:
                    product_option = ProductOptions.objects.get(product_option_code=item.product_option_code)
                    grouped_items[item.product_code].append({
                        'option_name': product_option.product_option_name,
                        'option_code': product_option.product_option_code,
                        'quantity': item.quantity,
                        'total_price': item.subtotal
                    })

                items = []
                for product_code, options in grouped_items.items():
                    product = Product.objects.get(product_code=product_code)
                    total_quantity = sum(option['quantity'] for option in options)
                    total_price = sum(option['total_price'] for option in options)
                    items.append({
                        'product_name': product.product_name,
                        'product_code': product.product_code,
                        'options': options,
                        'total_quantity': total_quantity,
                        'total_price': total_price
                    })

                return JsonResponse({'items': items})
            return JsonResponse({'items': []})
            
        elif data.get('code') == "get_order_cart_items":
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(member_id=request.user.username)
                items = []

                # 상품을 옵션별로 그룹화
                for item in cart_items:
                    product = Product.objects.get(product_code=item.product_code)
                    product_option = ProductOptions.objects.get(product_option_code=item.product_option_code)
                    items.append({
                        'product_name': product.product_name,
                        'product_code': product.product_code,
                        'product_thumbnail_image': product.product_thumbnail_image.url,
                        'option_name': product_option.product_option_name,
                        'option_code': product_option.product_option_code,
                        'quantity': item.quantity,
                        'total_price': item.subtotal
                    })

                pprint.pprint(items)

                return JsonResponse({'items': items})
            return JsonResponse({'items': []})
        
        elif data.get('code') == "remove_cart_item":
            member_id = request.user.username
            product_code = data.get('product_code')
            product_option_code = data.get('product_option_code')
            
            # 장바구니에서 해당 아이템 제거 로직 구현
            try:
                # CartItem을 필터링하여 삭제
                CartItem.objects.filter(
                    member_id=member_id,
                    product_code=product_code,
                    product_option_code=product_option_code
                ).delete()

                return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        
        elif data.get('code') == "get_user_info":
            user_info = {
                'name': request.user.last_name + request.user.first_name if request.user.last_name and request.user.first_name else request.user.username,
                'phone': request.user.phone_number if request.user.phone_number else "",
                'address_default': request.user.address_default if request.user.address_default else "",
                'address_detail': request.user.address_detail if request.user.address_detail else "",
                'address_code': request.user.address_code if request.user.address_code else ""
            }
            return JsonResponse({'user_info': user_info})

        elif data.get('code') == "confirm_order":
            pprint.pprint(data.get('order_data'))
            cart_items = CartItem.objects.filter(member_id=request.user.username)
            
            order_delivery_method = "롯데택배" if data.get('order_data').get('deliveryMethod') == "delivery" else "스토어픽업"  
            order_delivery_fee = 0 if order_delivery_method == "스토어픽업" else 3000
            order_deposit_bank_info = data.get('order_data').get('depositBank')
            order_deposit_name = data.get('order_data').get('depositName')
            
            try:
                for cart_item in cart_items:
                    user_name = request.user.username
                    order_code = generate_order_number()
                    order_number = generate_manual_order_number()
                    order_product_order_number = generate_manual_order_product_number()
                    
                    Order.objects.create(
                        order_consumer_id=user_name,
                        order_channel="수동주문",
                        order_code=order_code,
                        order_number=order_number,
                        order_product_order_number=order_product_order_number,
                        order_product_code = cart_item.product_code,
                        order_product_option_code=cart_item.product_option_code,
                        order_quantity=cart_item.quantity,
                        order_price=cart_item.subtotal,
                        order_delivery_method=order_delivery_method,
                        order_delivery_fee=order_delivery_fee,
                        order_status="입금대기",
                        order_deposit_bank_info=order_deposit_bank_info,
                        order_deposit_name=order_deposit_name,
                        order_payment_method="무통장입금",
                        order_payment_amount=cart_item.subtotal,
                        order_created_datetime=datetime.now(),
                        order_modified_datetime=datetime.now(),
                        order_receiver_name=data.get('order_data').get('recipientName'),
                        order_receiver_phone_number=data.get('order_data').get('recipientPhone'),
                        order_receiver_address=data.get('order_data').get('recipientAddressDefault'),
                        order_receiver_detail_address=data.get('order_data').get('recipientAddressDetail'),
                        order_receiver_message=data.get('order_data').get('recipientMessage')
                    )
                    cart_item.delete()
                    print(f'주문 생성 완료: {order_code}')
            except Exception as e:
                print(f'주문 생성 실패: {e}')
                return JsonResponse({'status': 'error', 'message': str(e)})
            return JsonResponse({'status': 'success'})


class DashboardProductHome(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/product/product_home.html"
    login_url = reverse_lazy("account_login")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        products = Product.objects.all()
        
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
                                category_code__in=str(row["상품분류 번호"]).split("|")
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
                            # The code snippet is checking if a specific URL
                            # ("https://ecimg.cafe24img.com/pg1094b33231538027/innovape/") is present
                            # in the value of the "이미지등록(상세)" key in the `row` dictionary. If the URL
                            # is found in the value, the `thumbnail_src` variable is assigned the
                            # value of the "이미지등록(상세)" key. If the URL is not found in the value, the
                            # `thumbnail_src` variable is assigned a different URL constructed by
                            # appending the value of the
                            if "https://ecimg.cafe24img.com/pg1094b33231538027/innovape/" in row["이미지등록(상세)"]:
                                thumbnail_src = row["이미지등록(상세)"]
                            else:
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
                                
                                if "https://ecimg.cafe24img.com/pg1094b33231538027/innovape/" in src:
                                    formatted_src = src.replace("https://ecimg.cafe24img.com/pg1094b33231538027/innovape/", "")
                                else:
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
                            if "52" in str(row["상품분류 번호"]).split("|"):
                                if "입호흡 액상" not in product_name:
                                    product_name += " 입호흡 액상"

                            if "45" in str(row["상품분류 번호"]).split("|"):
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
                        product_option_display_name=str(row["품목명"]),
                        defaults={
                            'product': product,
                            'product_option_code': product.product_code + str(option_index).zfill(4),
                            'product_option_title': option_title,
                            'product_option_name': option_name,
                            'product_option_stock': stock_quantity,
                            'product_option_price': option_price,
                            'product_option_cafe24_code': str(row["품목코드"]),
                        },
                    )

                return JsonResponse({'status': 'success'})
            except Exception as e:
                print(f"Error is : {e}")
                return JsonResponse({'status': 'error', 'message': str(e)})

        elif request.POST.get("code") == "set-manager-price":
            print("직원가 자동 세팅 시작")
            products = Product.objects.all()
            for product in products:
                 # 원래 계산식: ((판매가 - 공급가) * 0.4) + 공급가
                raw_price = ((product.product_sell_price - product.product_supply_price) * 0.4) + product.product_supply_price
                # 100원 단위 올림 처리
                rounded_price = math.ceil(raw_price / 100) * 100
                product.product_manager_price = rounded_price
                product.save()
            return JsonResponse({'status': 'success'})


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
            product_url = request.POST.get("product_url")

            if request.POST.get("mall") == "메두사":
                data = medusa_crawl(product_url)

            elif request.POST.get("mall") == "샤슈컴퍼니":
                data = siasiucp_crawl(product_url)

            return JsonResponse(
                {
                    "status": "success",
                    "data": data,
                }
            )

        elif request.POST.get("code") == "product_add":
            data = json.loads(request.POST.get("data"))

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
                    "product_origin_url": data["product_origin_url"],
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
        if request.POST.get("code") == "product_coupang_first_upload":
            try:
                products = Product.objects.filter(
                    Q(product_coupang_code__isnull=True) | Q(product_coupang_code=''),
                    product_coupang_is_prohibitted=False
                ).order_by('product_code').values_list('product_code', flat=True)
                
                # 엑셀 파일 생성
                print('엑셀 생성')
                excel_filename = coupang_product_upload(products)
                
                if excel_filename:
                    # ZIP 파일 생성을 위한 메모리 버퍼
                    zip_buffer = io.BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        # 엑셀 파일 추가
                        print('엑셀 추가')
                        excel_path = os.path.join(settings.MEDIA_ROOT, 'upload_forms', excel_filename)
                        zip_file.write(excel_path, excel_filename)
                        
                        # 선택된 상품들의 이미지 파일 추가
                        for product_code in products:
                            product = Product.objects.get(product_code=product_code)
                            
                            if product.product_origin_url:
                                data = check_origin_base_url(product.product_origin_url)
                                
                                # 썸네일 이미지 추가
                                print('썸네일 추가')
                                try:
                                    thumbnail_data, thumbnail_ext = convert_image(data['thumbnail_image_url'])
                                    thumbnail_image_name = f"{product_code}.{thumbnail_ext}"  # 이미지 이름 설정
                                    zip_file.writestr(f'images/thumbnails/{thumbnail_image_name}', thumbnail_data)  # ZIP 파일에 직접 추가
                                except Exception as e:
                                    print(f"썸네일 이미지 가져오기 실패: {e}")
                                    
                                # 상세 이미지 추가
                                print('상세페이지 추가')
                                for index, detail_image in enumerate(data['detail_image_urls']):
                                    try:
                                        detail_data, detail_ext = convert_image(detail_image)
                                        detail_image_name = f"{product_code}_{index}.{detail_ext}"
                                        zip_file.writestr(f'images/details/{detail_image_name}', detail_data)  # ZIP 파일에 직접 추가
                                    except Exception as e:
                                        print(f"상세 이미지 가져오기 실패: {e}")
                    
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

        elif request.POST.get("code") == "product_cafe24_first_upload":
            try:
                products = Product.objects.filter(
                    Q(product_cafe24_code__isnull=True) | Q(product_cafe24_code='')
                ).values_list('product_code', flat=True)
                
                print(f"Found {len(products)} products to process")
                today = datetime.now().strftime('%Y%m%d')
                
                # CSV 파일 생성 (이제 final_zip_buffer를 반환)
                final_zip_buffer = cafe24_product_upload(products)
                
                if final_zip_buffer:
                    # 이미지 파일들과 함께 ZIP 파일 생성
                    zip_buffer = io.BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        # 기존 ZIP 파일의 내용을 새 ZIP 파일에 추가
                        with zipfile.ZipFile(final_zip_buffer) as existing_zip:
                            for file_info in existing_zip.filelist:
                                zip_file.writestr(file_info.filename, existing_zip.read(file_info.filename))
                    
                    # ZIP 파일 응답 생성
                    zip_buffer.seek(0)
                    timestamp = time.strftime('%Y%m%d_%H%M%S')
                    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="cafe24_upload_package_{timestamp}.zip"'
                    
                    return response
                else:
                    return JsonResponse({'status': 'error', 'message': '파일 생성 실패'})
                    
            except Exception as e:
                print(f"Error in cafe24 upload: {str(e)}")
                print(traceback.format_exc())
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

        elif request.POST.get("code") == "product_cafe24_option_first_upload":
            try:
                products = Product.objects.all().values_list('product_code', flat=True)
                print(products)
                
                # CSV 파일 생성 및 파일명 반환
                result_filename = cafe24_option_upload(products)
                
                if result_filename:
                    return JsonResponse({
                        'status': 'success',
                        'filename': result_filename
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': '파일 생성 실패'
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        elif request.POST.get("code") == "selenium_test":
            try:
                #is_successed = medusa_crawl()
                
                return JsonResponse({'status': 'success', 'data': is_successed})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

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