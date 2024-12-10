from django.contrib import admin
from .models import Category, Product, ProductOptions, Consumer

# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'category_code', 'category_parent')
    search_fields = ('category_name',)
    list_filter = ('category_name',)

admin.site.register(Category, CategoryAdmin)
    

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_code', 'product_name', 'get_product_categories', 'product_consumer_price', 'product_sell_price', 'product_supply_price', 'product_author',)
    search_fields = ('product_name', 'product_code', 'product_alternative_price',)
    list_filter = ('product_name',)
    filter_horizontal = ('product_category', 'product_related_products',)

    def get_product_categories(self, obj):
        # Many-to-Many 관계의 항목들을 표시하는 방법
        return ", ".join([str(product) for product in obj.product_category.all()])
    
    get_product_categories.short_description = '상품 카테고리'

admin.site.register(Product, ProductAdmin)
    

class ProductOptionsAdmin(admin.ModelAdmin):
    list_display = ('product', 'product_option_cafe24_code', 'product_option_display_name', 'product_option_price', 'product_option_stock',)
    search_fields = ('product',)
    list_filter = ('product',)

admin.site.register(ProductOptions, ProductOptionsAdmin)


class ConsumerAdmin(admin.ModelAdmin):
    list_display = ('consumer_id', 'consumer_name', 'consumer_phone_number', 'consumer_birth', 'consumer_total_purchase', 'consumer_register_dt', 'consumer_verify_dt',)
    search_fields = ('consumer_id', 'consumer_name', 'consumer_phone_number',)
    list_filter = ('consumer_area', 'consumer_register_path',)

admin.site.register(Consumer, ConsumerAdmin)