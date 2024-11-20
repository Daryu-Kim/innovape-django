from django.db import models
from account.models import Member

# Create your models here.
class Category(models.Model):
    category_name = models.CharField(max_length=50, verbose_name='카테고리명')
    category_code = models.CharField(max_length=50, default='0', verbose_name='카테고리 코드')
    category_description = models.CharField(max_length=200, blank=True, verbose_name='카테고리 설명')
    category_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name='부모 카테고리')
    category_seo_title = models.CharField(max_length=100, blank=True, verbose_name='검색용 사이트 제목')
    category_seo_author = models.CharField(max_length=50, blank=True, verbose_name='검색용 게시자')
    category_seo_description = models.CharField(max_length=200, blank=True, verbose_name='검색용 요약설명')
    category_seo_keywords = models.CharField(max_length=500, blank=True, verbose_name='검색용 검색어')

    class Meta:
        verbose_name = "상품 카테고리"
        verbose_name_plural = "상품 카테고리"

    def __str__(self):
        return self.category_name

class Display(models.Model):
    display_name = models.CharField(max_length=50, verbose_name='진열방식명')
    display_description = models.CharField(max_length=100, verbose_name='진열방식 설명')
    display_code = models.CharField(max_length=50, unique=True, verbose_name='진열방식 코드')

    class Meta:
        verbose_name = "상품 진열방식"
        verbose_name_plural = "상품 진열방식"

    def __str__(self):
        return self.display_name

class Product(models.Model):
    product_cafe24_code = models.CharField(max_length=20, blank=True, verbose_name='카페24 상품코드')
    product_code = models.CharField(max_length=7, verbose_name='상품 분류코드')
    product_name = models.CharField(max_length=100, verbose_name='상품명')
    product_manage_name = models.CharField(max_length=100, verbose_name='상품명 (관리용)')
    product_category = models.ManyToManyField(Category, related_name='product_category', verbose_name='상품 카테고리')
    product_display = models.ManyToManyField(Display, related_name='product_display', verbose_name='상품 진열방식')
    product_description = models.CharField(max_length=200, verbose_name='상품 요약설명')
    product_detail = models.CharField(max_length=2000, verbose_name='상품 상세페이지')
    product_keywords = models.CharField(max_length=500, verbose_name='상품 검색어')
    product_consumer_price = models.PositiveIntegerField(verbose_name='상품 소비자가')
    product_sell_price = models.PositiveIntegerField(verbose_name='상품 판매가')
    product_supply_price = models.PositiveIntegerField(verbose_name='상품 공급가')
    product_alternative_price = models.CharField(max_length=50, blank=True, verbose_name='상품 판매가 대체 텍스트')
    product_thumbnail_image = models.BinaryField(verbose_name='상품 이미지')
    product_optional_products = models.ManyToManyField('self', blank=True, verbose_name='추가 상품 (같은 계열 상품)')
    product_related_products = models.ManyToManyField('self', blank=True, verbose_name='관련 상품 (추천 상품)')
    product_seo_title = models.CharField(max_length=100, blank=True, verbose_name='검색용 사이트 제목')
    product_seo_author = models.CharField(max_length=50, blank=True, verbose_name='검색용 게시자')
    product_seo_description = models.CharField(max_length=200, blank=True, verbose_name='검색용 요약설명')
    product_seo_keywords = models.CharField(max_length=500, blank=True, verbose_name='검색용 검색어')
    product_author = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, verbose_name='상품 게시자')

    class Meta:
        verbose_name = "상품"
        verbose_name_plural = "상품"

    def __str__(self):
        return self.product_name

class ProductOptions(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='상품')
    product_stock = models.IntegerField(default=0, verbose_name='상품 재고수량')
    product_option_title = models.CharField(max_length=50, blank=True, verbose_name='상품 옵션제목')
    product_option_name = models.CharField(max_length=50, verbose_name='상품 옵션명')
    product_option_display_name = models.CharField(max_length=100, verbose_name='상품 옵션명 (관리용)')
    product_option_price = models.IntegerField(default=0, verbose_name='상품 옵션가')
    
    class Meta:
        verbose_name = "상품 옵션"
        verbose_name_plural = "상품 옵션"

    def __str__(self):
        return self.product_option_display_name