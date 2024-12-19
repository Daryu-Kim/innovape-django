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


def medusa_crawl(product_url):
  try:
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    service = Service('chromedriver/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    print(config("MEDUSA_LOGIN_URL"))
    driver.get(config("MEDUSA_LOGIN_URL"))
    
    print(config("MEDUSA_LOGIN_ID"), config("MEDUSA_LOGIN_PASSWORD"))
    id = driver.find_element(By.ID, "member_id")
    passwd = driver.find_element(By.ID, "member_passwd")
    id.send_keys(config("MEDUSA_LOGIN_ID"))
    passwd.send_keys(config("MEDUSA_LOGIN_PASSWORD"))
    passwd.send_keys(Keys.ENTER)
    
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "cp500")))
    driver.get(product_url)
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
      driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
      time.sleep(3)
      new_height = driver.execute_script("return document.body.scrollHeight")
      if new_height == last_height:
        break
      last_height = new_height
      
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    options = []
    urls = []
    thumbnail_binary_data = None
    supply_price_text = None

    img_tags = soup.select("#prdDetail > div.cont img")
    thumbnail_img_tag = soup.select("#big_img_box > div > img")[0]
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
        opt = option.get_text(strip=True).replace(" [품절]", "")
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
            "Referer": config("MEDUSA_BASE_URL"),  # 요청을 보낸 페이지의 URL로 설정
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
            src = config("MEDUSA_BASE_URL") + src.replace("//", "/")

          try:
            headers = {
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
              "Referer": config("MEDUSA_BASE_URL"),  # 요청을 보낸 페이지의 URL로 설정
            }
            response = requests.get(src, headers=headers)
            response.raise_for_status()  # 요청 실패 시 예외 발생
            binary_data = response.content
            base64_encoded_data = base64.b64encode(binary_data).decode("utf-8")
            urls.append(f"data:image/jpeg;base64,{base64_encoded_data}")
          except requests.RequestException as e:
            print(f"Error fetching image from {src}: {e}")
            continue  # 오류가 발생한 경우 다음 이미지로 넘어감
    
    driver.quit()
    return {
      "detail_urls": urls,
      "thumbnail_binary_data": thumbnail_binary_data,
      "supply_price": supply_price_text,
      "options": options,
    }
  except Exception as e:
    print(e)
    return None

def siasiucp_crawl(product_url):
  
  try:
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    service = Service('chromedriver/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    print(config("SIASIUCP_LOGIN_URL"))
    driver.get(config("SIASIUCP_LOGIN_URL"))
    
    print(config("SIASIUCP_LOGIN_ID"), config("SIASIUCP_LOGIN_PASSWORD"))
    id = driver.find_element(By.ID, "member_id")
    passwd = driver.find_element(By.ID, "member_passwd")
    id.send_keys(config("SIASIUCP_LOGIN_ID"))
    passwd.send_keys(config("SIASIUCP_LOGIN_PASSWORD"))
    passwd.send_keys(Keys.ENTER)
    
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "index_ban_100")))
    driver.get(product_url)
    
    current_height = 0

    while True:
      driver.execute_script("window.scrollBy(0, 1000);")
      current_height += 1000
      new_height = driver.execute_script("return document.body.scrollHeight")
      time.sleep(1)
      if new_height <= current_height:
        time.sleep(1)
        break
      
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    options = []
    urls = []
    thumbnail_binary_data = None
    supply_price_text = None

    img_tags = soup.select("#prdDetail > div.cont img")
    thumbnail_img_tag = soup.select_one("#contents > div > div.xans-element-.xans-product.xans-product-detail.timesale-active > div.detailArea > div.xans-element-.xans-product.xans-product-image.imgArea > div.RW > div.prdImg > div.thumbnail > img")
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
        opt = option.get_text(strip=True).replace(" [품절]", "")
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
            "Referer": config("SIASIUCP_REFERER_URL"),  # 요청을 보낸 페이지의 URL로 설정
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
          if not src.startswith(
              "http://"
          ) and not src.startswith("https://"):
            src = "https:" + src

          try:
            headers = {
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
              "Referer": config("SIASIUCP_REFERER_URL"),  # 요청을 보낸 페이지의 URL로 설정
            }
            response = requests.get(src, headers=headers)
            response.raise_for_status()  # 요청 실패 시 예외 발생
            binary_data = response.content
            base64_encoded_data = base64.b64encode(binary_data).decode("utf-8")
            urls.append(f"data:image/jpeg;base64,{base64_encoded_data}")
          except requests.RequestException as e:
            print(f"Error fetching image from {src}: {e}")
            continue  # 오류가 발생한 경우 다음 이미지로 넘어감
    
    driver.quit()
    return {
      "detail_urls": urls,
      "thumbnail_binary_data": thumbnail_binary_data,
      "supply_price": supply_price_text,
      "options": options,
    }
  except Exception as e:
    print(e)
    return None
  
def coupang_test(product_url):
