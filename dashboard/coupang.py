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

def coupang_product_upload(product_codes):
  try:
    # 기기 정보 조회
    device_products = Product.objects.filter(product_code__in=product_codes, product_category__category_code__in=['43', '51', '50'])
    # 액상 정보 조회
    liquid_products = Product.objects.filter(product_code__in=product_codes, product_category__category_code__in=['52', '45'])
    # 무화기 / 팟 정보 조회
    pod_products = Product.objects.filter(product_code__in=product_codes, product_category__category_code__in=['124', '156'])
    # 코일 정보 조회
    coil_products = Product.objects.filter(product_code__in=product_codes, product_category__category_code__in=['157', '158'])
    # 악세사리 정보 조회
    accesory_products = Product.objects.filter(product_code__in=product_codes, product_category__category_code__in=['125'])
    
    # 템플릿 파일 경로
    template_path = os.path.join(settings.MEDIA_ROOT, 'document_forms', 'coupang_upload_form.xlsm')
    
    # 결과 파일 저장할 경로
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    result_dir = os.path.join(settings.MEDIA_ROOT, 'upload_forms')
    os.makedirs(result_dir, exist_ok=True)
    
    # 엑셀 파일 복사본 생성
    result_excel = os.path.join(result_dir, f'coupang_upload_result_{timestamp}.xlsm')
    
    # openpyxl로 파일 열기
    wb = openpyxl.load_workbook(template_path, keep_vba=True)  # keep_vba=True로 매크로 보존
    ws = wb.active  # 활성 시트 선택
    
    # 데이터 처리 및 결과 기록
    for index, row_num in enumerate(range(5, ws.max_row + 1)):  # 5행부터 처리
      try:
        # 셀 값 읽기
        product_code = ws.cell(row=row_num, column=1).value  # A열
        if not product_code:
            continue
        
        product = Product.objects.get(product_code=str(int(product_code)))
        
        # 처리 결과 기록
        ws.cell(row=row_num, column=ws.max_column + 1, value='SUCCESS')
        
      except Exception as e:
        # 에러 발생 시 결과 기록
        ws.cell(row=row_num, column=ws.max_column + 1, value=str(e))
        
    # 엑셀 파일 저장
    wb.save(result_excel)
    
  except Exception as e:
    print(e)
    return False
