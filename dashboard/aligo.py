import requests
import json
from decouple import config


def send_sms(phone_number_list, message, title):
    send_url = config("ALIGO_SEND_URL")

    phone_number_array = []
    for phone_number in phone_number_list:
        phone_number.replace('-', '')
        phone_number.replace(' ', '')
        phone_number_array.append(phone_number)
    
    phone_number_str = ','.join(phone_number_array)


    sms_data={
        'key': config("ALIGO_API_KEY"), #api key
        'userid': config("ALIGO_USER_ID"), # 알리고 사이트 아이디
        'sender': config("ALIGO_SENDER"), # 발신번호
        'receiver': phone_number_str, # 수신번호 (,활용하여 1000명까지 추가 가능)
        'msg': message, #문자 내용 
    }
    send_response = requests.post(send_url, data=sms_data)
    return send_response.json()

def sms_remain():
    remain_url = config("ALIGO_REMAIN_URL")

    remain_data = {
        'key' : config("ALIGO_API_KEY"),#api key 
        'userid' : config("ALIGO_USER_ID") # 알리고 사이트 아이디 
    }
    remain_response = requests.post(remain_url, data=remain_data)
    return remain_response.json()