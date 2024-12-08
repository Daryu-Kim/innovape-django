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
from dashboard.models import Product, ProductOptions
from django.conf import settings
import os
import mimetypes
from requests_toolbelt.multipart.encoder import MultipartEncoder
import http.client
import json
import random
import math


def login_check_view(request):
    if request.user.is_authenticated:
        return redirect("/dashboard/home")
    else:
        return redirect("/account/login")


def get_access_naver_info(request=None):
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
        return response.json()
    else:
        return None


def get_access_coupang_info():
    expires = datetime.strptime(config("COUPANG_SECRET_KEY_EXPIRES"), "%Y-%m-%d %H:%M")
    now = datetime.now()

    if expires > now:
        difference = expires - now
        days_left = difference.days
        return days_left
    else:
        return None


def get_access_interpark_info():
    # 인증키 발급 승인 후 개발 필요
    return None


def get_access_sixshop_info():
    return "MANUAL"

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


def get_access_cafe24_info():
    return "MANUAL"
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
    
def smartstore_product_upload(product_code, product_smartstore_code):
    token = get_access_naver_info()
    product = Product.objects.get(product_code=product_code)
    
    # 무작위 가격 인상률 계산 (15 ~ 40%)
    price_increase_rate = random.uniform(1.15, 1.40)
    increased_price = int(product.product_consumer_price * price_increase_rate)
    consumer_price = math.ceil(increased_price / 100) * 100
    
    # 상품 상세페이지 제작
    detail_html_parts = []
    for image_path in product.product_detail:
        # 전체 파일 경로 생성
        full_path = os.path.join(settings.MEDIA_ROOT, image_path)
        
        try:
            # 이미지 파일 정보 준비
            file_name = os.path.basename(image_path)
            mime_type, _ = mimetypes.guess_type(file_name)
            
            # 지원되는 이미지 형식 확인
            if not mime_type or not mime_type.startswith('image/') or  mime_type not in ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']:
                print(f"Unsupported image format: {mime_type} for {file_name}")
                continue
                
            with open(full_path, 'rb') as img_file:
                file_data = img_file.read()
                # 파일 크기 체크 (10MB 제한)
                if len(file_data) > 10 * 1024 * 1024:
                    print(f"File too large: {file_name}")
                    continue
            
            # 이미지 업로드를 위한 multipart 데이터 준비
            m = MultipartEncoder(fields={
                'imageFiles': (file_name, file_data, mime_type)
            })
            
            # 이미지 업로드 요청
            detail_conn = http.client.HTTPSConnection("api.commerce.naver.com")
            detail_headers = {
                'Authorization': f'{token["access_token"]}',
                'Content-Type': m.content_type
            }
            
            detail_conn.request("POST", "/external/v1/product-images/upload", m.to_string(), detail_headers)
            detail_res = detail_conn.getresponse()
            detail_data = json.loads(detail_res.read().decode('utf-8'))
            
            # 응답 데이터 디버깅
            print(f"Image upload response: {detail_data}")
            
            # rate limit 체크
            if detail_data.get('code') == 'GW.RATE_LIMIT':
                print("Rate limit reached, waiting for 1 second...")
                time.sleep(1)  # 1초 대기
                continue  # 현재 이미지 다시 시도
            
            # 이미지 URL 안전하게 추출
            images = detail_data.get('images', [])
            if images and len(images) > 0 and 'url' in images[0]:
                img_url = images[0]['url']
                img_tag = f'<img src="{img_url}" alt="상세 이미지">'
                detail_html_parts.append(img_tag)
            else:
                print(f"No valid image URL in response for {file_name}")
                # 잠시 대기 후 다음 이미지 처리
                time.sleep(0.5)
                continue
            
            # 성공적인 업로드 후 잠시 대기
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
            time.sleep(0.5)  # 에러 발생 시에도 대기
            continue
    
    # 카테고리 정보
    if product.product_category.filter(category_code="43") or product.product_category.filter(category_code="51"):
        category_id = "50006130"
    else:
        category_id = "50006131"
    
    # 썸네일 정보
    multipart_data = []
    file_name = product.product_thumbnail_image.name.split('/')[-1]
    file_data = product.product_thumbnail_image.read()
    mime_type, _ = mimetypes.guess_type(file_name)
    multipart_data.append(
        ('imageFiles', (file_name, file_data, mime_type))
    )
    
    m = MultipartEncoder(fields=multipart_data)
    
    thumbnail_conn = http.client.HTTPSConnection("api.commerce.naver.com")
    thumbnail_headers = {
        'Authorization': f"{token['access_token']}",
        'Content-Type': m.content_type
    }
    
    thumbnail_conn.request("POST", "/external/v1/product-images/upload", m.to_string(), thumbnail_headers)
    thumbnail_res = thumbnail_conn.getresponse()
    thumbnail_data = json.loads(thumbnail_res.read().decode('utf-8'))
    thumbnail_url = thumbnail_data.get('images', [])[0]['url']

    # 옵션 정보
    product_options = ProductOptions.objects.filter(product=product)
    product_options_data = []
    for index, option in enumerate(product_options):
        option_price = option.product_option_price
        if option_price < 0:
            option_price = 0
        
        product_options_data.append({
            "id": option.product_option_smartstore_code,
            "optionName1": option.product_option_display_name.split("/")[0],
            "optionName2": option.product_option_display_name.split("/")[1],
            "stockQuantity": option.product_option_stock,
            "sellerManagerCode": option.product_option_code,
            "price": option_price,
        })
        
    product_data = {
        "originProduct": {
            "statusType": "SALE",
            "leafCategoryId": category_id,
            "name": product.product_seo_title.replace("[", "").replace("]", ""),
            "detailContent": f'<div class="product-detail-images">{"".join(detail_html_parts)}</div>',
            "images": {
                "representativeImage": {
                    "url": thumbnail_url,
                }
            },
            "salePrice": consumer_price,
            "stockQuantity": 99999999,
            "deliveryInfo": {
                "deliveryType": "DELIVERY",
                "deliveryAttributeType": "NORMAL",
                "deliveryCompany": "HYUNDAI",
                "quickServiceAreas": ["DAEJEON"],
                "visitAddressId": 106281415,
                "deliveryFee": {
                    "deliveryFeeType": "CONDITIONAL_FREE",
                    "baseFee": 3000,
                    "freeConditionalAmount": 50000,
                    "deliveryFeePayType": "PREPAID",
                    "deliveryFeeByArea": {
                        "deliveryAreaType": "AREA_3",
                        "area2extraFee": 3000,
                        "area3extraFee": 3000
                    }
                },
                "claimDeliveryInfo": {
                    "returnDeliveryCompanyPriorityType": "PRIMARY",
                    "returnDeliveryFee": 3000,
                    "exchangeDeliveryFee": 6000,
                    "shippingAddressId": 106281415,
                    "returnAddressId": 106281416,
                },
                "todayStockQuantity": 99999999,
                "customProductAfterOrderYn": False,
            },
            "detailAttribute": {
                "naverShoppingSearchInfo": {
                    "manufacturerName": product.product_name.split("[")[1].split("]")[0],
                    "brandName": product.product_name.split("[")[1].split("]")[0],
                },
                "afterServiceInfo": {
                    "afterServiceTelephoneNumber": "010-4486-7410",
                    "afterServiceGuideContent": "교환/반품의 경우 단순변심은 수령 후 1일 이내, 상품 하자는 수령 후 3일 이내에 가능합니다.",
                },
                "originAreaInfo": {
                    "originAreaCode": "00",
                },
                "sellerCodeInfo": {
                    "sellerManagementCode": product.product_code,
                },
                "optionInfo": {
                    "optionCombinationSortType": "CREATE",
                    "optionCombinationGroupNames": {
                        "optionGroupName1": "출고방식 선택",
                        "optionGroupName2": product_options[0].product_option_title,
                    },
                    "optionCombinations": product_options_data,
                    "useStockManagement": True,
                },
                "eventParaseCont": product.product_description,
                "minorPurchasable": False,
                "productInfoProvidedNotice": {
                    "productInfoProvidedNoticeType": "ETC",
                    "etc": {
                        "afterServiceDirector": "010-4486-7410",
                        "itemName": product.product_name.split("] ")[1],
                        "modelName": product.product_name.split("] ")[1],
                        "manufacturer": product.product_name.split("[")[1].split("]")[0],
                    }
                },
                "seoInfo": {
                    "pageTitle": product.product_seo_title,
                    "metaDescription": product.product_seo_description,
                    "sellerTags": [
                        {"text": keyword.strip()} 
                        for keyword in product.product_smartstore_keywords.split(",")
                        if keyword.strip()
                    ]
                },
            },
            "customerBenefit": {
                "immediateDiscountPolicy": {
                    "discountMethod": {
                        "value": consumer_price - product.product_sell_price,
                        "unitType": "WON",
                    }
                },
                "purchasePointPolicy": {
                    "value": 3,
                    "unitType": "PERCENT",
                },
                "reviewPointPolicy": {
                    "textReviewPoint": round(product.product_sell_price * 0.005 / 10) * 10,  # 10원 단위로 반올림
                    "photoVideoReviewPoint": round(product.product_sell_price * 0.01 / 10) * 10,
                    "afterUseTextReviewPoint": round(product.product_sell_price * 0.01 / 10) * 10,
                    "afterUsePhotoVideoReviewPoint": round(product.product_sell_price * 0.02 / 10) * 10,
                    "storeMemberReviewPoint": round(product.product_sell_price * 0.0025 / 10) * 10  # 10원 단위로 반올림
                }
            }
        },
        "smartstoreChannelProduct": {
            "channelProductName": product.product_seo_title.replace("[", "").replace("]", ""),
            "naverShoppingRegistration": True,
            "channelProductDisplayStatusType": "ON"
        }
    }
    
    conn = http.client.HTTPSConnection("api.commerce.naver.com")
    
    upload_headers = {
        'Authorization': f"{token['access_token']}",
        'Content-Type': "application/json"
    }
    if product_smartstore_code:
        conn.request("POST", "/external/v2/products", json.dumps(product_data), headers=upload_headers)
    else:
        conn.request("PUT", f"/external/v2/products/origin-products/{product_smartstore_code}", json.dumps(product_data), headers=upload_headers)
    response = conn.getresponse()
    response_data = json.loads(response.read().decode("utf-8"))
    print(response_data)
    
    if 'originProductNo' in response_data:
        product.product_smartstore_code = str(response_data['originProductNo'])
        product.product_smartstore_channel_code = str(response_data['smartstoreChannelProductNo'])
        product.save()
    else:
        print(f"Error in product upload: {response_data}")
    
    option_conn = http.client.HTTPSConnection("api.commerce.naver.com")
    option_headers = {
        'Authorization': f"{token['access_token']}",
    }
    option_conn.request("GET", f"/external/v2/products/origin-products/{response_data['originProductNo']}", headers=option_headers)
    option_res = option_conn.getresponse()
    option_data = json.loads(option_res.read().decode("utf-8"))
    
    for get_option in option_data['originProduct']['detailAttribute']['optionInfo']['optionCombinations']:
        product_option = ProductOptions.objects.filter(product=product, product_option_display_name=f"{get_option['optionName1']}/{get_option['optionName2']}").first()
        product_option.product_option_smartstore_code = get_option['id']
        product_option.save()
    # 성공 응답
    return "SUCCESS"