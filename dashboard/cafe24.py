import os
import time
import hmac
import hashlib
import math
import random
from django.db.models import Q
from django.http import JsonResponse
from dashboard.models import Product, ProductOptions
from decouple import config
import pandas as pd
from django.conf import settings
import openpyxl as op
from PIL import Image
import io
import zipfile
import shutil
from datetime import datetime


def create_resized_images(product_codes):
    try:
        # 기본 경로 설정
        today = datetime.now().strftime('%Y%m%d')
        
        # 임시 폴더 생성
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_product_images')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 썸네일 이미지용 사이즈 설정
        sizes = {
            'big': (500, 500),
            'medium': (300, 300),
            'small': (220, 220),
            'tiny': (100, 100)
        }
        
        # 썸네일 이미지 폴더 생성
        for size_name, size_dims in sizes.items():
            size_path = os.path.join(temp_dir, size_name, today)
            os.makedirs(size_path, exist_ok=True)
            
        # NNEditor 폴더 생성
        nneditor_path = os.path.join(temp_dir, 'NNEditor', today)
        os.makedirs(nneditor_path, exist_ok=True)
        
        for product_code in product_codes:
            try:
                product = Product.objects.get(product_code=product_code)
                
                # 썸네일 이미지 처리
                if product.product_thumbnail_image:
                    original_path = os.path.join(settings.MEDIA_ROOT, str(product.product_thumbnail_image))
                    _, ext = os.path.splitext(original_path)
                    
                    with Image.open(original_path) as img:
                        for size_name, size_dims in sizes.items():
                            resized_path = os.path.join(
                                temp_dir,
                                size_name,
                                today,
                                f"{product_code}{ext}"
                            )
                            
                            resized_img = img.copy()
                            resized_img.thumbnail(size_dims, Image.Resampling.LANCZOS)
                            resized_img.save(resized_path, quality=95, optimize=True)
                
                # 상세 이미지 처리
                if product.product_detail:
                    for detail_image in product.product_detail:
                        try:
                            # 원본 이미지 경로
                            original_path = os.path.join(settings.MEDIA_ROOT, detail_image)
                            
                            # 원본 파일명 추출
                            original_filename = os.path.basename(detail_image)
                            
                            # NNEditor 폴더에 복사
                            target_path = os.path.join(nneditor_path, original_filename)
                            
                            # 파일 복사
                            shutil.copy2(original_path, target_path)
                            
                        except Exception as e:
                            print(f"Error processing detail image {detail_image}: {e}")
                            continue
                            
            except Exception as e:
                print(f"Error processing product {product_code}: {e}")
                continue
        
        # ZIP 파일 생성
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zip_file.write(file_path, arcname)
        
        # 임시 폴더 삭제
        shutil.rmtree(temp_dir)
        
        # ZIP 파일 반환
        zip_buffer.seek(0)
        return zip_buffer
        
    except Exception as e:
        print(f"Error in create_resized_images: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return None

def cafe24_product_upload(product_codes):
    try:
        today = datetime.now().strftime('%Y%m%d')
        # 템플릿 파일 경로
        template_path = os.path.join(settings.MEDIA_ROOT, 'document_forms', 'cafe24_upload_form.csv')
        
        # 결과 파일 저장할 경로
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        result_dir = os.path.join(settings.MEDIA_ROOT, 'upload_forms')
        os.makedirs(result_dir, exist_ok=True)
        
        template_df = pd.read_csv(template_path, encoding='utf-8-sig')

        new_rows = []
        
        # 상품 데이터 처리
        for product_code in product_codes:
            try:
                product = Product.objects.get(product_code=product_code)
                product_options = ProductOptions.objects.filter(product=product)
                
                # 옵션 데이터 생성
                # 1. 고정 문자열
                fixed_option = "출고 방법 선택{빠른 출고 [2영업일 이내 출고]|순차 출고 [4영업일 이내 출고]}//"
                
                # 2. 컬러 선택 옵션 생성
                # - 첫 번째 옵션의 타이틀 가져오기
                option_title = product_options.first().product_option_title if product_options.exists() else "컬러 선택"
                
                # - 빠른 출고를 제외한 옵션명들 가져오기
                option_names = [
                    opt.product_option_name 
                    for opt in product_options 
                    if "빠른 출고" not in opt.product_option_display_name 
                    and "빠른출고" not in opt.product_option_display_name
                ]
                
                # - 옵션 문자열 생성
                color_option = f"{option_title}{{{'|'.join(option_names)}}}"
                
                # 3. 최종 옵션 문자열 생성
                final_option = fixed_option + color_option
                
                # HTML 상세설명 생성
                detail_html = '<div class="product_detail">'
                if product.product_detail:
                    for detail_image in product.product_detail:
                        # 파일명과 확장자 추출
                        filename = os.path.basename(detail_image)
                        # HTML img 태그 생성 (경로를 today/filename 형식으로)
                        detail_html += f'<img src="https://ecimg.cafe24img.com/pg1094b33231538027/innovape/web/upload/NNEditor/{today}/{filename}" alt="{product.product_name}">'
                detail_html += '</div>'
                
                # 무작위 가격 인상률 계산 (15 ~ 40%)
                price_increase_rate = random.uniform(1.15, 1.40)
                increased_price = int(product.product_consumer_price * price_increase_rate)
                consumer_price = math.ceil(increased_price / 100) * 100
                
                row = template_df.iloc[0].copy()  # 템플릿의 첫 번째 행을 복사
                category_codes = '|'.join(product.product_category.values_list('category_code', flat=True))
                
                # 데이터 업데이트
                row['자체 상품코드'] = product.product_code
                row['진열상태'] = 'Y'
                row['판매상태'] = 'Y'
                row['상품분류 번호'] = category_codes
                row['상품분류 신상품영역'] = 'N|N'
                row['상품분류 추천상품영역'] = 'N|N'
                row['상품명'] = product.product_name
                row['상품명(관리용)'] = product.product_name
                row['상품 요약설명'] = product.product_description
                row['상품 간략설명'] = product.product_description
                row['상품 상세설명'] = detail_html
                row['검색어설정'] = product.product_keywords
                row['과세구분'] = 'A|10'
                row['소비자가'] = consumer_price
                row['공급가'] = product.product_supply_price
                row['상품가'] = math.floor(product.product_sell_price * 10 / 11)
                row['판매가'] = product.product_sell_price
                row['판매가 대체문구 사용'] = 'Y' if product.product_alternative_price else 'N'
                row['판매가 대체문구'] = product.product_alternative_price if product.product_alternative_price else ''
                row['주문수량 제한 기준'] = 'O'
                row['최소 주문수량(이상)'] = '1'
                row['적립금'] = '1.00'
                row['적립금 구분'] = 'P'
                row['공통이벤트 정보'] = 'Y'
                row['성인인증'] = 'N'
                row['옵션사용'] = 'T'
                row['품목 구성방식'] = 'T'
                row['옵션 표시방식'] = 'S'
                row['옵션입력'] = final_option
                row['필수여부'] = 'F|F'
                row['추가입력옵션'] = 'F'
                row['이미지등록(상세)'] = f'{today}/{product_thumbnail_image.split("/")[-1]}'
                row['이미지등록(목록)'] = f'{today}/{product_thumbnail_image.split("/")[-1]}'
                row['이미지등록(작은목록)'] = f'{today}/{product_thumbnail_image.split("/")[-1]}'
                row['이미지등록(축소)'] = f'{today}/{product_thumbnail_image.split("/")[-1]}'
                row['제조사'] = 'M0000000'
                row['공급사'] = 'S0000000'
                row['브랜드'] = 'B0000000'
                row['트렌드'] = 'T0000000'
                row['자체분류 코드'] = 'C000000A'
                row['유효기간 사용여부'] = 'F'
                row['원산지'] = '1798'
                row['상품결제안내'] = '''
고액결제의 경우 안전을 위해 카드사에서 확인전화를 드릴 수도 있습니다. 확인과정에서 도난 카드의 사용이나 타인 명의의 주문등 정상적인 주문이 아니라고 판단될 경우 임의로 주문을 보류 또는 취소할 수 있습니다.  

무통장 입금은 상품 구매 대금은 PC뱅킹, 인터넷뱅킹, 텔레뱅킹 혹은 가까운 은행에서 직접 입금하시면 됩니다.  
주문시 입력한 입금자명과 실제입금자의 성명이 반드시 일치하여야 하며, 7일 이내로 입금을 하셔야 하며 입금되지 않은 주문은 자동취소 됩니다.'''
                row['상품배송안내'] ='''
- 산간벽지나 도서지방은 별도의 추가금액을 지불하셔야 하는 경우가 있습니다.
고객님께서 주문하신 상품은 입금 확인후 배송해 드립니다. 다만, 상품종류에 따라서 상품의 배송이 다소 지연될 수 있습니다.'''
                row['교환/반품안내'] = '''
교환 및 반품 주소
- #supplier_return_address_info#

교환 및 반품이 가능한 경우
- 계약내용에 관한 서면을 받은 날부터 7일. 단, 그 서면을 받은 때보다 재화등의 공급이 늦게 이루어진 경우에는 재화등을 공급받거나 재화등의 공급이 시작된 날부터 7일 이내
- 공급받으신 상품 및 용역의 내용이 표시.광고 내용과 다르거나 계약내용과 다르게 이행된 때에는 당해 재화 등을 공급받은 날 부터 3월이내, 그사실을 알게 된 날 또는 알 수 있었던 날부터 30일이내

교환 및 반품이 불가능한 경우
- 이용자에게 책임 있는 사유로 재화 등이 멸실 또는 훼손된 경우(다만, 재화 등의 내용을 확인하기 위하여 포장 등을 훼손한 경우에는 청약철회를 할 수 있습니다)
- 이용자의 사용 또는 일부 소비에 의하여 재화 등의 가치가 현저히 감소한 경우
- 시간의 경과에 의하여 재판매가 곤란할 정도로 재화등의 가치가 현저히 감소한 경우
- 복제가 가능한 재화등의 포장을 훼손한 경우
- 개별 주문 생산되는 재화 등 청약철회시 판매자에게 회복할 수 없는 피해가 예상되어 소비자의 사전 동의를 얻은 경우
- 디지털 콘텐츠의 제공이 개시된 경우, (다만, 가분적 용역 또는 가분적 디지털콘텐츠로 구성된 계약의 경우 제공이 개시되지 아니한 부분은 청약철회를 할 수 있습니다.)

※ 고객님의 마음이 바뀌어 교환, 반품을 하실 경우 상품반송 비용은 고객님께서 부담하셔야 합니다.
(색상 교환, 사이즈 교환 등 포함)'''
                row['배송정보'] = 'F'
                row['배송기간'] = '3|7'
                row['검색엔진최적화(SEO) 검색엔진 노출 설정'] = 'Y'
                row['검색엔진최적화(SEO) Title'] = product.product_seo_title
                row['검색엔진최적화(SEO) Author'] = product.product_seo_author
                row['검색엔진최적화(SEO) Description'] = product.product_seo_description
                row['검색엔진최적화(SEO) Keywords'] = product.product_seo_keywords
                row['검색엔진최적화(SEO) 상품 이미지 Alt 텍스트'] = product.product_name
                row['상품배송유형 코드'] = 'C'
                row['스토어픽업 설정'] = 'N'
                row['상품 전체중량(kg)'] = '1.00'

                new_rows.append(row)
                    
            except Exception as e:
                print(f"Error processing product {product_code}: {e}")
                continue
        
        # 새로운 DataFrame 생성
        result_df = pd.DataFrame(new_rows)
        
        # 이미지 리사이징 및 ZIP 파일 생성
        zip_buffer = create_resized_images(product_codes)
        
        if zip_buffer:
            # CSV 파일과 이미지 ZIP 파일을 하나의 ZIP 파일로 묶기
            final_zip_buffer = io.BytesIO()
            with zipfile.ZipFile(final_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as final_zip:
                # CSV 파일 추가
                final_zip.writestr(f'cafe24_upload_result_{timestamp}.csv', result_df.to_csv(index=False, encoding='utf-8-sig'))
                
                # 이미지 ZIP 파일 추가
                final_zip.writestr('product_images.zip', zip_buffer.getvalue())
            
            final_zip_buffer.seek(0)
            return final_zip_buffer
            
        return None
        
    except Exception as e:
        print(e)
        return None

def cafe24_option_upload(product_codes):
    try:
        # 템플릿 파일 경로
        option_template_path = os.path.join(settings.MEDIA_ROOT, 'document_forms', 'cafe24_option_upload_form.csv')
        
        # 결과 파일 저장할 경로
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        result_dir = os.path.join(settings.MEDIA_ROOT, 'upload_forms')
        os.makedirs(result_dir, exist_ok=True)
        
        option_template_df = pd.read_csv(option_template_path, encoding='utf-8-sig')
        option_new_rows = []
        
        # 상품 옵션 데이터 처리
        for product_code in product_codes:
            try:
                product = Product.objects.get(product_code=product_code)
                product_options = ProductOptions.objects.filter(product=product).order_by('product_option_code')

                # 총재고량 계산
                total_stock = sum(opt.product_option_stock for opt in product_options)

                for product_option in product_options:
                    row = option_template_df.iloc[0].copy()  # 템플릿의 첫 번째 행을 복사

                    row['상품코드'] = product.product_cafe24_code
                    row['자체 상품코드'] = product.product_code
                    row['상품명'] = product.product_name
                    row['판매가'] = product.product_sell_price
                    row['총 재고량'] = total_stock
                    row['품목코드'] = product_option.product_option_cafe24_code
                    row['품목명'] = product_option.product_option_display_name
                    row['자체 품목코드'] = product_option.product_option_code
                    row['재고관리 사용'] = 'T'
                    row['재고수량'] = product_option.product_option_stock
                    row['안전재고'] = '0'
                    row['재고관리 등급'] = 'A'
                    row['수량체크 기준'] = 'B'
                    row['품목 진열상태'] = 'T'
                    row['품목 판매상태'] = 'T'
                    row['품절표시 사용'] = 'T' if product_option.product_option_stock <= 0 else 'F'
                    row['옵션 추가금액'] = product_option.product_option_price

                    new_rows.append(row)
                    
            except Exception as e:
                print(f"Error processing product {product_code}: {e}")
                continue

        option_result_df = pd.DataFrame(option_new_rows)

        # 결과 파일 저장
        result_csv = os.path.join(result_dir, f'cafe24_option_upload_result_{timestamp}.csv')
        option_result_df.to_csv(result_csv, index=False, encoding='utf-8-sig')
        
        return f'cafe24_option_upload_result_{timestamp}.csv'
        
    except Exception as e:
        print(f"Error in cafe24_option_upload: {e}")
        return None