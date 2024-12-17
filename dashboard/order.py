from .models import Order
from datetime import datetime

def generate_order_number():
  order = Order.objects.filter(order_created_datetime__date=datetime.now().date()).order_by('-order_code').first()
  date = datetime.now().strftime("%Y%m%d")
  if order:
    code = int(order.order_code[-4:])
    return f'ORDCODE{date}{code+1:04d}'
  else:
    return f'ORDCODE{date}0001'

def generate_manual_order_number():
  order = Order.objects.filter(order_created_datetime__date=datetime.now().date()).order_by('-order_code').first()
  date = datetime.now().strftime("%Y%m%d")
  if order:
    code = int(order.order_code[-4:])
    return f'ORD{date}{code+1:04d}'
  else:
    return f'ORD{date}0001'
  
def generate_manual_order_product_number():
  order = Order.objects.filter(order_created_datetime__date=datetime.now().date()).order_by('-order_code').first()
  date = datetime.now().strftime("%Y%m%d")
  if order:
    code = int(order.order_code[-4:])
    return f'PORD{date}{code+1:04d}'
  else:
    return f'PORD{date}0001'


