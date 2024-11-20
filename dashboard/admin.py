from django.contrib import admin
from .models import Category, Display, Product, ProductOptions

# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'category_code', 'category_parent')
    search_fields = ('category_name',)
    list_filter = ('category_name',)

    # readonly_fields = ('category_seo_author',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not obj:
            form.base_fields['category_seo_title'].initial = " - 이노베이프 INNOVAPE"
            form.base_fields['category_seo_author'].initial = "이노베이프 INNOVAPE"
            form.base_fields['category_seo_keywords'].initial = "이노베이프,전자담배,전담,"
        
        return form

admin.site.register(Category, CategoryAdmin)
    

class DisplayAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'display_code')
    search_fields = ('display_name',)
    list_filter = ('display_name',)

admin.site.register(Display, DisplayAdmin)
    

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'get_product_categories', 'get_product_displays', 'product_consumer_price', 'product_sell_price', 'product_supply_price', 'product_author',)
    search_fields = ('product_name',)
    list_filter = ('product_name',)
    filter_horizontal = ('product_category', 'product_display', 'product_optional_products', 'product_related_products',)

    def get_product_categories(self, obj):
        # Many-to-Many 관계의 항목들을 표시하는 방법
        return ", ".join([str(product) for product in obj.product_category.all()])
    
    def get_product_displays(self, obj):
        # 마찬가지로 다른 Many-to-Many 관계 필드
        return ", ".join([str(product) for product in obj.product_display.all()])
    
    get_product_categories.short_description = '상품 카테고리'
    get_product_displays.short_description = '상품 진열방식'

admin.site.register(Product, ProductAdmin)
    

class ProductOptionsAdmin(admin.ModelAdmin):
    list_display = ('product_option_display_name', 'product_option_price', 'product_stock', 'product',)
    search_fields = ('product',)
    list_filter = ('product',)

admin.site.register(ProductOptions, ProductOptionsAdmin)