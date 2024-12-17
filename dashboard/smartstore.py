from innovape.views import get_access_naver_info
import http.client
from datetime import datetime, timedelta
import pprint
import requests
import time
import random
from dashboard.models import Consumer, Order
from .order import generate_order_number

def get_smartstore_order_all():
  token = get_access_naver_info()
  
  conn = http.client.HTTPSConnection("api.commerce.naver.com")
  headers = { 'Authorization': f'{token["access_token"]}' }
  conn.request("GET", "/external/v1/pay-order/seller/orders/2021123115350911/product-order-ids", headers=headers)

  res = conn.getresponse()
  data = res.read()

  print(data.decode("utf-8"))
  
def get_smartstore_orders():
  base_url = 'https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders'
  token = get_access_naver_info()
  now = datetime.now()
  
  from_days = 30
  to_days = 29
  
  try:
    while to_days > 0:
      pprint.pprint(f"from_days: {from_days}, to_days: {to_days}")
      from_date = (now - timedelta(days=from_days)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+09:00'
      to_date = (now - timedelta(days=to_days)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+09:00'
      params = {
        'from': from_date,
        'to': to_date,
        'rangeType': 'PAYED_DATETIME',
        'productOrderStatuses': ','.join(set(['PAYED'])),
        'claimStatues': 'CANCEL_REQUEST',
        'placeOrderStatusType': 'NOT_YET',
      }
      
      headers = {
          'Authorization': f'{token["access_token"]}',  # 인증 토큰
          'Content-Type': 'application/json'
      }
      
      response = requests.get(base_url, headers=headers, params=params)
      response.raise_for_status()
      data = response.json()
      
      for order in data.get('data').get('contents'):
        if Order.objects.filter(order_channel='스마트스토어', order_product_order_number=order.get('content').get('productOrderId')).exists():
          # 이미 있는 주문
          continue
        else:
          total_purchase = order.get('content').get('order').get('chargeAmountPaymentAmount', 0) + order.get('content').get('order').get('checkoutAccumulationPaymentAmount', 0) + order.get('content').get('order').get('generalPaymentAmount', 0) + order.get('content').get('order').get('naverMileagePaymentAmount', 0)

          # 없는 주문
          if Consumer.objects.filter(consumer_channel='스마트스토어', consumer_id=order.get('content').get('content').get('order').get('ordererId')).exists():
            # 고객이 있는 경우
            consumer = Consumer.objects.filter(consumer_channel='스마트스토어', consumer_id=order.get('content').get('order').get('ordererId')).first()
            consumer.consumer_total_visits += 1
            consumer.consumer_total_orders += 1
            consumer.consumer_total_purchase += total_purchase
            consumer.consumer_last_order_dt = order.get('content').get('order').get('paymentDate')
            consumer.consumer_last_connection_dt = order.get('content').get('order').get('paymentDate')
            consumer.save()
          else:
            # 고객이 없는 경우
            register_path = '모바일' if order.get('content').get('order').get('payLocationType') == 'MOBILE' else 'PC'
            
            Consumer.objects.create(
              consumer_id=order.get('content').get('order').get('ordererId'),
              consumer_channel='스마트스토어',
              consumer_grade='노바',
              consumer_name=order.get('content').get('order').get('ordererName'),
              consumer_phone_number=order.get('content').get('order').get('ordererTel'),
              consumer_email=order.get('content').get('order').get('ordererId')+'@naver.com',
              consumer_verify_info="스마트스토어 인증 완료",
              consumer_verify_dt=datetime.now(),
              consumer_birth="",
              consumer_area='',
              consumer_base_address='',
              consumer_detail_address='',
              consumer_refund_account='',
              consumer_total_visits=1,
              consumer_total_orders=1,
              consumer_total_purchase=total_purchase,
              consumer_last_order_dt=order.get('content').get('order').get('paymentDate'),
              consumer_last_connection_dt=order.get('content').get('order').get('paymentDate'),
              consumer_register_dt=order.get('content').get('order').get('paymentDate'),
              consumer_register_path=register_path,
            )
            
          Order.objects.create(
            order_consumer_id=order.get('content').get('order').get('ordererId'),
            order_channel='스마트스토어',
            order_code=generate_order_number(),
            order_number=order.get('content').get('order').get('orderId'),
            order_product_order_number=order.get('productOrderId'),
            order_product_code=order.get('content').get('productOrder').get(),
            order_product_option_code='',
            order_quantity='',
            order_price='',
          )
        
      from_days -= 1
      to_days -= 1
      
      time.sleep(random.uniform(0.55, 0.75))
    
    return True
  except Exception as e:
    pprint.pprint(f"주문 정보 가져오기 오류: {e}")
    return False
