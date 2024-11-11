from django.db import models

# Create your models here.
class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    category_description = models.CharField(max_length=200, blank=True)
    category_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    category_seo_title = models.CharField(max_length=100, blank=True)
    category_seo_author = models.CharField(max_length=50, blank=True)
    category_seo_description = models.CharField(max_length=200, blank=True)
    category_seo_keywords = models.CharField(max_length=500, blank=True)

class Display(models.Model):
    display_name = models.CharField(max_length=50)

class Product(models.Model):
    product_code = models.CharField(max_length=7)
    product_name = models.CharField(max_length=100)
    product_manage_name = models.CharField(max_length=100)
    product_category = models.ManyToManyField(Category, related_name='product_category')
    product_display = models.ManyToManyField(Display, related_name='product_display')
    product_description = models.CharField(max_length=200)
    product_detail = models.CharField(max_length=2000)
    product_keywords = models.CharField(max_length=500)
    product_consumer_price = models.PositiveIntegerField()
    product_sell_price = models.PositiveIntegerField()
    product_supply_price = models.PositiveIntegerField()
    product_alternative_price = models.CharField(max_length=50, blank=True)
    
