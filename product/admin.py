from django.contrib import admin
from .models import CustomUser, Product, ProductStock, History, Units

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff', 'is_superuser')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'product_name', 'product_type', 'product_quantity', 'price')
    
class ProductStockAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'product_quantity')

class HistoryAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'product_quantity')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductStock, ProductStockAdmin)
admin.site.register(History, HistoryAdmin)
admin.site.register(Units)
