from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, ProductOptions

@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_product_cache(sender, **kwargs):
  cache.delete('recommended_products')
  cache.delete('new_products')
  cache.delete('all_products')
  cache.delete('recommended_products_options')
  cache.delete('new_products_options')
  cache.delete('all_product_options')