from django.contrib.auth.models import AbstractUser
from django.db import models

class Member(AbstractUser):
    # 추가 필드를 정의할 수 있습니다.
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username
