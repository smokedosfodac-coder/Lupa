
from django.contrib import admin
import nested_admin
from django.contrib.auth.admin import UserAdmin
from .models import Product, ColorVariant, VariantImage, Address, Order, CustomUser
from django_summernote.admin import SummernoteModelAdmin
from .models import ContactMessage
from .models import Coupon

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Adiciona o campo 'cpf' à tela de edição do usuário no admin
    fieldsets = UserAdmin.fieldsets + (
        ('Campos Personalizados', {'fields': ('cpf',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('cpf',)}),
    )


class VariantImageInline(nested_admin.NestedTabularInline):
    model = VariantImage
    extra = 1

class ColorVariantInline(nested_admin.NestedTabularInline):
    model = ColorVariant
    inlines = [VariantImageInline]
    extra = 1

# store/admin.py

# ... (seus outros imports e classes Inline) ...

class ProductAdmin(nested_admin.NestedModelAdmin, SummernoteModelAdmin):
    summernote_fields = ('description',)
    inlines = [ColorVariantInline]
    # Estas linhas controlam a lista de produtos no admin
    list_display = ('name', 'price', 'has_capacity_options')
    list_editable = ('has_capacity_options',) # Permite editar a opção diretamente na lista

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'created_at')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')

class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'active', 'valid_from', 'valid_to']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']

if admin.site.is_registered(Product):
    admin.site.unregister(Product)


# REGISTRO ÚNICO E FINAL - SEM VERIFICAÇÕES
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Address)
admin.site.register(Order)
admin.site.register(Coupon, CouponAdmin)