from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Product, Category, RubberColor, LensType, ProductLensImage, CustomUser, Address, ContactMessage
from django_summernote.admin import SummernoteModelAdmin

# Configuração para as imagens das lentes dentro do produto
class LensImageInline(admin.TabularInline):
    model = ProductLensImage
    extra = 1

class ProductAdmin(SummernoteModelAdmin):
    list_display = ('name', 'price', 'category')
    search_fields = ('name',)
    summernote_fields = ('description',)
    filter_horizontal = ('available_rubbers',) 
    inlines = [LensImageInline]

# Registrar tudo
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(RubberColor)
admin.site.register(LensType)
admin.site.register(Address)        # Adicionado
admin.site.register(ContactMessage) # Adicionado