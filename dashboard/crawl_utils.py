from selenium import webdriver
from decouple import config
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import requests
import base64
import json
import platform
from PIL import Image
from io import BytesIO
from .models import Product

service = Service('chromedriver/chromedriver.exe') if platform.system() == 'Windows' else Service('chromedriver/chromedriver')
chrome_options = webdriver.ChromeOptions()
if platform.system() != 'Windows' and platform.system() != 'Darwin':
  chrome_options.add_argument('--headless')

def get_crawl_parameters(product_url):
    if product_url.startswith("https://medusamall.com/"):
        return (
            config("MEDUSA_BASE_URL"),
            config("MEDUSA_LOGIN_URL"),
            config("MEDUSA_LOGIN_URL"),
            "member_id",
            "member_passwd",
            config("MEDUSA_LOGIN_ID"),
            config("MEDUSA_LOGIN_PASSWORD"),
            "cp500",
            "#big_img_box > div > img",
            "#span_product_price_text",
            "#product_option_id1 > optgroup > option",
            "#prdDetail > div.cont img"
        )
    elif product_url.startswith("https://siasiucp.cafe24.com/"):
        return (
            config("SIASIUCP_BASE_URL"),
            config("SIASIUCP_LOGIN_URL"),
            config("SIASIUCP_REFERER_URL"),
            "member_id",
            "member_passwd",
            config("SIASIUCP_LOGIN_ID"),
            config("SIASIUCP_LOGIN_PASSWORD"),
            "index_ban_100",
            "#contents > div > div.xans-element-.xans-product.xans-product-detail.timesale-active > div.detailArea > div.xans-element-.xans-product.xans-product-image.imgArea > div.RW > div.prdImg > div.thumbnail > img",
            "#span_product_price_text",
            "#product_option_id1 > optgroup > option",
            "#prdDetail > div.cont img"
        )
    elif product_url.startswith("https://vanomshop.kr/"):
        return (
            config("VANOM_BASE_URL"),
            config("VANOM_LOGIN_URL"),
            config("VANOM_REFERER_URL"),
            "member_id",
            "member_passwd",
            config("VANOM_LOGIN_ID"),
            config("VANOM_LOGIN_PASSWORD"),
            "half",
            "img.ThumbImage",
            "#span_product_price_text",
            "#product_option_id1 > optgroup > option",
            "#prdDetail img"
        )
    else:
        raise ValueError("지원하지 않는 URL입니다.")

def crawl_product(product_url):
    try:
        base_url,\
        login_url,\
        referer_url,\
        id_selector,\
        pw_selector,\
        login_id,\
        login_password,\
        class_name,\
        thumbnail_selector,\
        supply_price_selector,\
        option_selector,\
        detail_selector, = get_crawl_parameters(product_url)
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print(login_url)
        driver.get(login_url)
        
        print(login_id, login_password)
        id = driver.find_element(By.ID, id_selector)
        passwd = driver.find_element(By.ID, pw_selector)
        id.send_keys(login_id)
        passwd.send_keys(login_password)
        passwd.send_keys(Keys.ENTER)
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))
        driver.get(product_url)
        
        current_height = 0

        while True:
            driver.execute_script("window.scrollBy(0, 1000);")
            current_height += 1000
            new_height = driver.execute_script("return document.body.scrollHeight")
            time.sleep(1)
            if new_height <= current_height:
                break
            
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        options = []
        urls = []
        thumbnail_binary_data = None
        supply_price_text = None

        thumbnail_image_url = ""
        detail_image_urls = []

        img_tags = soup.select(detail_selector)
        thumbnail_img_tag = soup.select(thumbnail_selector)[0]
        supply_price_tag = soup.select_one(supply_price_selector)
        option_tags = soup.select(option_selector)

        if not option_tags:
            option_tags = soup.select(option_selector.replace('optgroup', ''))

        # 공급가 크롤링
        if supply_price_tag:
            supply_price_text = supply_price_tag.get_text(strip=True)
            if len(supply_price_text) > 0:
                supply_price_text = supply_price_text.replace(",", "")
                supply_price_text = supply_price_text[:-1]

        # 옵션 크롤링
        if option_tags:
            for option in option_tags:
                opt = option.get_text(strip=True).replace(" [품절]", "")
                if opt:
                    options.append(opt)

        # 썸네일 크롤링
        thumbnail_src = thumbnail_img_tag.get("src")
        if thumbnail_src:
            if thumbnail_src.startswith("data:image/"):  # Base64 이미지 처리
                header, encoded = thumbnail_src.split(",", 1)
                thumbnail_binary_data = base64.b64decode(encoded)
            else:  # URL 방식의 이미지 처리
                if not thumbnail_src.startswith("http://") and not thumbnail_src.startswith("https://"):
                    thumbnail_src = "https:" + thumbnail_src

                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Referer": referer_url,  # 요청을 보낸 페이지의 URL로 설정
                    }
                    response = requests.get(thumbnail_src, headers=headers)
                    response.raise_for_status()  # 요청 실패 시 예외 발생
                    base64_encoded_data = base64.b64encode(response.content).decode("utf-8")
                    json_data = json.dumps({"image_data": base64_encoded_data})
                    loaded_data = json.loads(json_data)
                    thumbnail_binary_data = loaded_data["image_data"]
                except requests.RequestException as e:
                    print(f"Error fetching image from {thumbnail_src}: {e}")

        thumbnail_image_url = thumbnail_src

        # 상세페이지 크롤링
        for img in img_tags:
            src = img.get("src")
            if src:
                if src.startswith("data:image/"):  # Base64 이미지 처리
                    header, encoded = src.split(",", 1)
                    binary_data = base64.b64decode(encoded)
                else:  # URL 방식의 이미지 처리
                    if not src.startswith("http://") and not src.startswith("https://"):
                        src = base_url + src.replace("//", "/")

                    try:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                            "Referer": referer_url,  # 요청을 보낸 페이지의 URL로 설정
                        }
                        response = requests.get(src, headers=headers)
                        response.raise_for_status()  # 요청 실패 시 예외 발생
                        binary_data = response.content
                        base64_encoded_data = base64.b64encode(binary_data).decode("utf-8")
                        urls.append(f"data:image/jpeg;base64,{base64_encoded_data}")
                    except requests.RequestException as e:
                        print(f"Error fetching image from {src}: {e}")
                        continue  # 오류가 발생한 경우 다음 이미지로 넘어감
            detail_image_urls.append(src)
        
        driver.quit()
        return {
            "detail_urls": urls,
            "thumbnail_binary_data": thumbnail_binary_data,
            "supply_price": supply_price_text,
            "options": options,
            'thumbnail_image_url': thumbnail_image_url,
            'detail_image_urls': detail_image_urls
        }
    except Exception as e:
        print(e)
        return None

def get_header_by_base_url(product_url):
  if product_url.startswith("https://medusamall.com/"):
    headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
      "Referer": config("MEDUSA_BASE_URL"),  # 요청을 보낸 페이지의 URL로 설정
    }
  elif product_url.startswith("https://siasiucp.cafe24.com/"):
    headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
      "Referer": config("SIASIUCP_REFERER_URL"),  # 요청을 보낸 페이지의 URL로 설정
    }
  elif product_url.startswith("https://vanomshop.kr/"):
    headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
      "Referer": config("VANOM_REFERER_URL"),  # 요청을 보낸 페이지의 URL로 설정
    }
  
  return headers
  
def convert_image(product_origin_url):
  try:
    headers = get_header_by_base_url(product_origin_url)
    response = requests.get(product_origin_url, headers=headers)
    response.raise_for_status()  # 요청 실패 시 예외 발생
    image = Image.open(BytesIO(response.content))
    
    # GIF 파일인 경우 JPG로 변환
    output = BytesIO()
    image = image.convert('RGB')  # RGB로 변환 (GIF 포함)
    image.save(output, format='JPEG')  # JPEG로 저장
    return output.getvalue(), 'jpg'  # 변환된 이미지 데이터와 확장자 반환
  except Exception as e:
    print(f"Error processing image from {product_origin_url}: {e}")
    return None, None
  
def convert_origin_url_to_product(datas):
  try:
    for data in datas:
      print(data)
      product = Product.objects.get(product_code=data['상품코드'])
      product.product_origin_url = data['URL']
      product.save()
    return True
  except Exception as e:
    print(f'ERROR: {e}')
    return False