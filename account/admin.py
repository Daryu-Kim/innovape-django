from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Member

class MemberAdmin(UserAdmin):
    model = Member
    # 필요한 필드를 추가합니다.
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'address_default', 'address_detail', 'address_code')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'address_default', 'address_detail', 'address_code')}),
    )

admin.site.register(Member, MemberAdmin)
