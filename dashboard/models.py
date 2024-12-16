from django.db import models
from account.models import Member
from django.contrib.postgres.fields import ArrayField

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
    product_smartstore_code = models.CharField(max_length=20, blank=True, verbose_name='스마트스토어 상품코드')
    product_smartstore_channel_code = models.CharField(max_length=20, blank=True, verbose_name='스마트스토어 상품채널코드')
    product_coupang_code = models.CharField(max_length=20, blank=True, verbose_name='쿠팡 상품코드')
    product_esm_plus_code = models.CharField(max_length=50, blank=True, verbose_name='ESM+ 상품코드')
    product_esm_plus_gmarket_code = models.CharField(max_length=50, blank=True, verbose_name='ESM+ 지마켓 상품코드')
    product_esm_plus_auction_code = models.CharField(max_length=50, blank=True, verbose_name='ESM+ 옥션 상품코드')
    product_code = models.CharField(max_length=7, unique=True, verbose_name='상품 분류코드')
    product_name = models.CharField(max_length=100, verbose_name='상품명')
    product_manage_name = models.CharField(max_length=100, verbose_name='상품명 (관리용)')
    product_category = models.ManyToManyField(Category, related_name='product_category', verbose_name='상품 카테고리')
    product_description = models.CharField(max_length=200, blank=True, verbose_name='상품 요약설명')
    product_detail = ArrayField(models.CharField(max_length=2000), blank=True, verbose_name='상품 상세페이지')
    product_origin_detail = ArrayField(models.CharField(max_length=10000), default=list, blank=True, verbose_name='상품 원본 상세페이지')
    product_option = models.CharField(max_length=1000, blank=True, verbose_name='상품 옵션')
    product_keywords = models.CharField(max_length=1000, blank=True, verbose_name='상품 검색어')
    product_smartstore_keywords = models.CharField(max_length=1000, blank=True, verbose_name='스마트스토어 검색어')
    product_coupang_keywords = models.CharField(max_length=1000, blank=True, verbose_name='쿠팡 검색어')
    product_consumer_price = models.PositiveIntegerField(default=0, verbose_name='상품 소비자가')
    product_sell_price = models.PositiveIntegerField(default=0, verbose_name='상품 판매가')
    product_supply_price = models.PositiveIntegerField(default=0, verbose_name='상품 공급가')
    product_alternative_price = models.CharField(max_length=50, blank=True, verbose_name='상품 판매가 대체 텍스트')
    product_manager_price = models.PositiveIntegerField(default=0, verbose_name='상품 관리자가')
    product_thumbnail_image = models.ImageField(upload_to='product_thumbnail_images/', verbose_name='상품 이미지')
    product_origin_thumbnail_image = models.CharField(max_length=1000, blank=True, verbose_name='상품 원본 이미지')
    product_related_products = models.ManyToManyField('self', blank=True, verbose_name='관련 상품 (추천 상품)')
    product_seo_title = models.CharField(max_length=100, blank=True, verbose_name='검색용 사이트 제목')
    product_seo_author = models.CharField(max_length=50, blank=True, verbose_name='검색용 게시자')
    product_seo_description = models.CharField(max_length=200, blank=True, verbose_name='검색용 요약설명')
    product_seo_keywords = models.CharField(max_length=1000, blank=True, verbose_name='검색용 검색어')
    product_author = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, verbose_name='상품 게시자')
    product_created_datetime = models.DateTimeField(null=True, blank=True, verbose_name='상품 게시일자')
    product_modified_datetime = models.DateTimeField(null=True, blank=True, verbose_name='상품 수정일자')
    product_cafe24_is_prohibitted = models.BooleanField(default=False, verbose_name='카페24 제한 여부')
    product_smartstore_is_prohibitted = models.BooleanField(default=False, verbose_name='스마트스토어 제한 여부')
    product_coupang_is_prohibitted = models.BooleanField(default=False, verbose_name='쿠팡 제한 여부')
    product_esm_plus_is_prohibitted = models.BooleanField(default=False, verbose_name='ESM+ 제한 여부')
    product_esm_plus_gmarket_is_prohibitted = models.BooleanField(default=False, verbose_name='ESM+ 지마켓 제한 여부')
    product_esm_plus_auction_is_prohibitted = models.BooleanField(default=False, verbose_name='ESM+ 옥션 제한 여부')
    product_is_recommend = models.BooleanField(default=False, verbose_name='상품 추천 여부')
    product_is_new = models.BooleanField(default=False, verbose_name='상품 신상품 여부')

    class Meta:
        verbose_name = "상품"
        verbose_name_plural = "상품"

    def __str__(self):
        return self.product_name

class ProductOptions(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='상품')
    product_option_code = models.CharField(max_length=20, blank=True, verbose_name='상품 옵션 코드', unique=True)
    product_option_smartstore_code = models.CharField(max_length=20, blank=True, verbose_name='상품 옵션 스마트스토어 코드')
    product_option_cafe24_code = models.CharField(max_length=20, blank=True, verbose_name='상품 옵션 카페24 코드')
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

    CHANNEL_CHOICE = [
        ('스마트스토어', '스마트스토어'),
        ('카페24', '카페24'),
        ('쿠팡', '쿠팡'),
        ('ESM+', 'ESM+'),
        ('ESM+ 지마켓', 'ESM+ 지마켓'),
        ('ESM+ 옥션', 'ESM+ 옥션'),
        ('수동주문', '수동주문'),
    ]

    consumer_id = models.CharField(max_length=30, unique=True, verbose_name='고객 아이디')
    consumer_channel = models.CharField(max_length=30, choices=CHANNEL_CHOICE, default='카페24', verbose_name='고객 채널')
    consumer_grade = models.CharField(max_length=30, choices=GRADE_CHOICE, default='노바', verbose_name='고객 등급')
    consumer_name = models.CharField(max_length=50, verbose_name='고객 이름')
    consumer_phone_number = models.CharField(max_length=20, verbose_name='고객 전화번호')
    consumer_email = models.CharField(max_length=50, verbose_name='고객 이메일')
    consumer_verify_info = models.CharField(max_length=100, blank=True, verbose_name='고객 인증정보') # 이름/주민번호앞자리/주민번호뒷자리/발급일자
    consumer_verify_dt = models.DateField(blank=True, null=True, verbose_name='고객 인증일자')
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
    consumer_register_path = models.CharField(max_length=10, choices=REGISTER_PATH_CHOICE, default='모바일', verbose_name='고객 가입경로')
    
    class Meta:
        verbose_name = "고객"
        verbose_name_plural = "고객"

    def __str__(self):
        return self.consumer_id
    
class CartItem(models.Model):
    member_id = models.CharField(max_length=30, verbose_name='회원 아이디')
    product_code = models.CharField(max_length=30, verbose_name='상품 코드')
    product_option_code = models.CharField(max_length=30, verbose_name='상품 옵션 코드')
    quantity = models.PositiveIntegerField(default=1, verbose_name='수량')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    modified_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        verbose_name = "장바구니 아이템"
        verbose_name_plural = "장바구니 아이템"

    def __str__(self):
        return f"{self.member_id} - {self.product_code} ({self.product_option_code})"
    
    @property
    def subtotal(self):
        """상품 소계 금액 (상품가격 + 옵션가격) * 수량"""
        # 상품과 옵션의 가격을 가져오기 위해 Product와 ProductOptions 모델을 쿼리해야 합니다.
        product = Product.objects.get(product_code=self.product_code)
        product_option = ProductOptions.objects.get(product_option_code=self.product_option_code)

        return (product.product_manager_price + product_option.product_option_price) * self.quantity


class Order(models.Model):
    ORDER_STATUS_CHOICE = [
        ('입금대기', '입금대기'),
        ('상품발주대기', '상품발주대기'),
        ('상품발주완료', '상품발주완료'),
        ('상품검수중', '상품검수중'),
        ('상품검수완료', '상품검수완료'),
        ('상품포장중', '상품포장중'),
        ('상품포장완료', '상품포장완료'),
        ('발송대기', '발송대기'),
        ('발송완료', '발송완료'),
        ('배송중', '배송중'),
        ('배송완료', '배송완료'),
        ('취소요청', '취소요청'),
        ('취소완료', '취소완료'),
        ('환불요청', '환불요청'),
        ('환불완료', '환불완료'),
        ('교환요청', '교환요청'),
        ('교환완료', '교환완료'),
    ]

    ORDER_DELIVERY_METHOD_CHOICE = [
        ('롯데택배', '롯데택배'),
        ('GS 반값택배', 'GS 반값택배'),
        ('CU 반값택배', 'CU 반값택배'),
        ('스토어픽업', '스토어픽업'),
    ]

    ORDER_CHANNEL_CHOICE = [
        ('스마트스토어', '스마트스토어'),
        ('카페24', '카페24'),
        ('쿠팡', '쿠팡'),
        ('ESM+', 'ESM+'),
        ('ESM+ 지마켓', 'ESM+ 지마켓'),
        ('ESM+ 옥션', 'ESM+ 옥션'),
        ('수동주문', '수동주문'),
    ]
    
    order_consumer = models.ForeignKey(Consumer, on_delete=models.SET_NULL, null=True, verbose_name='주문 고객')
    order_channel = models.CharField(max_length=30, choices=ORDER_CHANNEL_CHOICE, default='수동주문', verbose_name='주문 채널')
    order_code = models.CharField(max_length=30, unique=True, verbose_name='주문 관리용 코드')
    order_number = models.CharField(max_length=30, blank=True, verbose_name='주문번호')
    order_product_order_number = models.CharField(max_length=30, blank=True, verbose_name='상품주문번호')
    order_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name='주문 상품')
    order_product_option = models.ForeignKey(ProductOptions, on_delete=models.SET_NULL, null=True, verbose_name='주문 상품 옵션')
    order_quantity = models.PositiveIntegerField(default=1, verbose_name='주문 수량')
    order_price = models.IntegerField(default=0, verbose_name='주문 가격')
    order_delivery_method = models.CharField(max_length=30, choices=ORDER_DELIVERY_METHOD_CHOICE, default='롯데택배', verbose_name='주문 배송방법')
    order_tracking_number = models.CharField(max_length=30, blank=True, verbose_name='주문 운송장번호')
    order_delivery_fee = models.PositiveIntegerField(default=0, verbose_name='주문 배송비')
    order_status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICE, default='입금대기', verbose_name='주문 상태')
    order_deposit_bank_info = models.CharField(max_length=200, blank=True, verbose_name='주문 입금은행 정보')
    order_deposit_name = models.CharField(max_length=30, blank=True, verbose_name='주문 입금자명')
    order_payment_method = models.CharField(max_length=30, blank=True, verbose_name='주문 결제방법')
    order_payment_amount = models.PositiveIntegerField(default=0, blank=True, verbose_name='주문 결제금액')
    order_created_datetime = models.DateTimeField(auto_now_add=True, verbose_name='주문 생성일시')
    order_modified_datetime = models.DateTimeField(auto_now=True, verbose_name='주문 수정일시')
    order_payment_completed_datetime = models.DateTimeField(blank=True, null=True, verbose_name='주문 결제완료일시')
    order_delivery_expected_datetime = models.DateTimeField(blank=True, null=True, verbose_name='주문 예상배송일시')
    order_delivery_started_datetime = models.DateTimeField(blank=True, null=True, verbose_name='주문 배송시작일시')
    order_delivery_completed_datetime = models.DateTimeField(blank=True, null=True, verbose_name='주문 배송완료일시')
    order_receiver_name = models.CharField(max_length=30, blank=True, verbose_name='주문 수취인명')
    order_receiver_phone_number = models.CharField(max_length=30, blank=True, verbose_name='주문 수취인 전화번호')
    order_receiver_address = models.CharField(max_length=200, blank=True, verbose_name='주문 수취인 주소')
    order_receiver_detail_address = models.CharField(max_length=100, blank=True, verbose_name='주문 수취인 상세주소')
    order_receiver_message = models.CharField(max_length=200, blank=True, verbose_name='주문 수취인 배송메시지')

    class Meta:
        verbose_name = "주문"
        verbose_name_plural = "주문"

    def __str__(self):
        return self.order_code


class Settle(models.Model):
    SETTLE_STATUS_CHOICE = [
        ('정산대기', '정산대기'),
        ('정산완료', '정산완료'),
        ('정산취소', '정산취소'),
    ]

    settle_order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='정산 주문')
    settle_amount = models.IntegerField(default=0, verbose_name='정산 금액')
    settle_status = models.CharField(max_length=30, choices=SETTLE_STATUS_CHOICE, default='정산대기', verbose_name='정산 상태')
    settle_expected_datetime = models.DateTimeField(blank=True, null=True, verbose_name='정산 예상일시')
    settle_completed_datetime = models.DateTimeField(blank=True, null=True, verbose_name='정산 완료일시')
    settle_created_datetime = models.DateTimeField(auto_now_add=True, verbose_name='정산 생성일시')
    settle_modified_datetime = models.DateTimeField(auto_now=True, verbose_name='정산 수정일시')

    class Meta:
        verbose_name = "정산"
        verbose_name_plural = "정산"

    def __str__(self):
        return self.settle_order.order_code

