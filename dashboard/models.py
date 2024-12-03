from django.db import models
from account.models import Member

# Create your models here.
class Category(models.Model):
    category_name = models.CharField(max_length=50, verbose_name='카테고리명')
    category_code = models.CharField(max_length=50, default='0', verbose_name='카테고리 코드')
    category_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name='부모 카테고리')

    class Meta:
        verbose_name = "상품 카테고리"
        verbose_name_plural = "상품 카테고리"

    def __str__(self):
        return self.category_name

class Product(models.Model):
    product_cafe24_code = models.CharField(max_length=20, blank=True, verbose_name='카페24 상품코드')
    product_code = models.CharField(max_length=7, unique=True, verbose_name='상품 분류코드')
    product_name = models.CharField(max_length=100, verbose_name='상품명')
    product_manage_name = models.CharField(max_length=100, verbose_name='상품명 (관리용)')
    product_category = models.ManyToManyField(Category, related_name='product_category', verbose_name='상품 카테고리')
    product_description = models.CharField(max_length=200, verbose_name='상품 요약설명')
    product_detail = models.CharField(max_length=2000, verbose_name='상품 상세페이지')
    product_keywords = models.CharField(max_length=500, verbose_name='상품 검색어')
    product_consumer_price = models.PositiveIntegerField(verbose_name='상품 소비자가')
    product_sell_price = models.PositiveIntegerField(verbose_name='상품 판매가')
    product_supply_price = models.PositiveIntegerField(verbose_name='상품 공급가')
    product_alternative_price = models.CharField(max_length=50, blank=True, verbose_name='상품 판매가 대체 텍스트')
    product_thumbnail_image = models.BinaryField(verbose_name='상품 이미지')
    product_related_products = models.ManyToManyField('self', blank=True, verbose_name='관련 상품 (추천 상품)')
    product_seo_title = models.CharField(max_length=100, blank=True, verbose_name='검색용 사이트 제목')
    product_seo_author = models.CharField(max_length=50, blank=True, verbose_name='검색용 게시자')
    product_seo_description = models.CharField(max_length=200, blank=True, verbose_name='검색용 요약설명')
    product_seo_keywords = models.CharField(max_length=500, blank=True, verbose_name='검색용 검색어')
    product_author = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, verbose_name='상품 게시자')
    product_created_datetime = models.DateTimeField(null=True, blank=True, verbose_name='상품 게시일자')
    product_modified_datetime = models.DateTimeField(null=True, blank=True, verbose_name='상품 수정일자')

    class Meta:
        verbose_name = "상품"
        verbose_name_plural = "상품"

    def __str__(self):
        return self.product_name
    
    def set_product_detail(self, product_detail_list):
        self.product_detail = ",".join(product_detail_list)

    def get_product_detail(self):
        return self.product_detail.split(",") if self.product_detail else []


class ProductOptions(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='상품')
    product_option_code = models.CharField(max_length=20, blank=True, verbose_name='상품 옵션코드')
    product_option_stock = models.IntegerField(default=0, verbose_name='상품 재고수량')
    product_option_title = models.CharField(max_length=50, blank=True, verbose_name='상품 옵션제목')
    product_option_name = models.CharField(max_length=50, verbose_name='상품 옵션명')
    product_option_display_name = models.CharField(max_length=100, verbose_name='상품 옵션명 (관리용)')
    product_option_price = models.IntegerField(default=0, verbose_name='상품 옵션가')
    
    class Meta:
        verbose_name = "상품 옵션"
        verbose_name_plural = "상품 옵션"

    def __str__(self):
        return self.product_option_display_name
    
class Consumer(models.Model):
    GRADE_CHOICE = [
        ('노바', '노바'),
        ('오닉스', '오닉스'),
        ('실버', '실버'),
        ('골드', '골드'),
        ('플래티넘', '플래티넘'),
        ('티타늄', '티타늄'),
        ('블랙 다이아몬드', '블랙 다이아몬드'),
    ]
    
    VERIFIED_CHOICE = [
        ('T', '인증됨'),
        ('F', '인증안됨'),
    ]
    
    AREA_CHOICE = [
        ('경기', '경기'),
        ('서울', '서울'),
        ('인천', '인천'),
        ('강원', '강원'),
        ('충남', '충남'),
        ('충북', '충북'),
        ('대전', '대전'),
        ('경북', '경북'),
        ('경남', '경남'),
        ('대구', '대구'),
        ('부산', '부산'),
        ('울산', '울산'),
        ('전북', '전북'),
        ('전남', '전남'),
        ('광주', '광주'),
        ('세종', '세종'),
        ('제주', '제주'),
        ('해외', '해외'),
    ]
    
    REGISTER_PATH_CHOICE = [
        ('PC', 'PC'),
        ('모바일', '모바일'),
    ]

    consumer_id = models.CharField(max_length=30, unique=True, verbose_name='고객 아이디')
    consumer_grade = models.CharField(max_length=30, choices=GRADE_CHOICE, default='노바', verbose_name='고객 등급')
    consumer_name = models.CharField(max_length=50, verbose_name='고객 이름')
    consumer_phone_number = models.CharField(max_length=20, verbose_name='고객 전화번호')
    consumer_email = models.CharField(max_length=50, verbose_name='고객 이메일')
    consumer_verified = models.CharField(max_length=10, choices=VERIFIED_CHOICE, default='F', verbose_name='고객 인증여부')
    consumer_birth = models.DateField(verbose_name='고객 생년월일')
    consumer_area = models.CharField(max_length=10, choices=AREA_CHOICE, blank=True, verbose_name='고객 거주지역')
    consumer_base_address = models.CharField(max_length=200, verbose_name='고객 기본주소')
    consumer_detail_address = models.CharField(max_length=100, blank=True, verbose_name='고객 상세주소')
    consumer_refund_account = models.CharField(max_length=50, blank=True, verbose_name='고객 환불계좌정보')
    consumer_total_visits = models.IntegerField(default=0, verbose_name='고객 총 방문횟수')
    consumer_total_orders = models.IntegerField(default=0, verbose_name='고객 총 실주문건수')
    consumer_total_purchase = models.IntegerField(default=0, verbose_name='고객 총 구매금액')
    consumer_last_order_dt = models.DateTimeField(blank=True, null=True, verbose_name='고객 최종주문일')
    consumer_last_connection_dt = models.DateTimeField(blank=True, null=True, verbose_name='고객 최종접속일')
    consumer_register_dt = models.DateField(verbose_name='고객 회원가입일')
    consumer_register_path = models.CharField(max_length=10, choices=REGISTER_PATH_CHOICE, verbose_name='고객 가입경로')
    
    class Meta:
        verbose_name = "고객"
        verbose_name_plural = "고객"

    def __str__(self):
        return self.consumer_id