from django.contrib.auth.models import AbstractUser
from django.db import models

class Member(AbstractUser):
    # 추가 필드를 정의할 수 있습니다.
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="우편번호") # 우편번호
    address_default = models.CharField(max_length=255, blank=True, null=True, verbose_name="기본주소") # 기본주소
    address_detail = models.CharField(max_length=255, blank=True, null=True, verbose_name="상세주소") # 상세주소

    def __str__(self):
        return self.username
