import os
import time
import hmac
import hashlib
import traceback
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
                print(f"Error processing product {product_code} [create_resized_images]: {e}")
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
        if not os.path.exists(template_path):
            print(f"Template file not found: {template_path}")
            return None
        
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
                
                row = {}
                category_codes = '|'.join(product.product_category.values_list('category_code', flat=True))
                category_n = '|'.join(['N'] * product.product_category.count())
                
                # 데이터 업데이트
                row['자체 상품코드'] = product.product_code
                row['진열상태'] = 'Y'
                row['판매상태'] = 'Y'
                row['상품분류 번호'] = category_codes
                row['상품분류 신상품영역'] = category_n
                row['상품분류 추천상품영역'] = category_n
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
                row['이미지등록(상세)'] = f'{today}/{str(product.product_thumbnail_image).split("/")[-1]}'
                row['이미지등록(목록)'] = f'{today}/{str(product.product_thumbnail_image).split("/")[-1]}'
                row['이미지등록(작은목록)'] = f'{today}/{str(product.product_thumbnail_image).split("/")[-1]}'
                row['이미지등록(축소)'] = f'{today}/{str(product.product_thumbnail_image).split("/")[-1]}'
                row['제조사'] = 'M0000000'
                row['공급사'] = 'S0000000'
                row['브랜드'] = 'B0000000'
                row['트렌드'] = 'T0000000'
                row['자체분류 코드'] = 'C000000A'
                row['유효기간 사용여부'] = 'F'
                row['원산지'] = '1798'
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
                print(f"Error processing product {product_code} [cafe24_product_upload]: {e}")
                continue
            
        # 새로운 DataFrame 생성 시 템플릿의 컬럼 순서 유지
        result_df = pd.DataFrame(new_rows, columns=template_df.columns)

        # CSV 저장 시 인코딩 확인
        csv_data = result_df.to_csv(index=False, encoding='utf-8-sig')
                
        # 이미지 리사이징 및 ZIP 파일 생성
        zip_buffer = create_resized_images(product_codes)
        
        if zip_buffer:
            # CSV 파일과 이미지 ZIP 파일을 하나의 ZIP 파일로 묶기
            final_zip_buffer = io.BytesIO()
            with zipfile.ZipFile(final_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as final_zip:
                # CSV 파일 추가 (바이트로 변환)
                csv_data = result_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                final_zip.writestr(f'cafe24_upload_result_{timestamp}.csv', csv_data)
                
                # 이미지 ZIP 파일 추가
                final_zip.writestr('product_images.zip', zip_buffer.getvalue())
            
            final_zip_buffer.seek(0)
            return final_zip_buffer
            
        return None
        
    except Exception as e:
        print(f"Error in cafe24_product_upload: {str(e)}")
        print(traceback.format_exc())  # 상세 에러 스택 출력
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
                    row = {}

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
                    row['총 누적판매량'] = ''

                    option_new_rows.append(row)
                    
            except Exception as e:
                print(f"Error processing product {product_code} [cafe24_option_upload]: {e}")
                continue

        option_result_df = pd.DataFrame(option_new_rows)

        # 결과 파일 저장
        result_filename = f'cafe24_option_upload_result_{timestamp}.csv'
        result_path = os.path.join(result_dir, result_filename)
        option_result_df.to_csv(result_path, index=False, encoding='utf-8-sig')
        
        return result_filename
        
    except Exception as e:
        print(f"Error in cafe24_option_upload: {e}")
        return None