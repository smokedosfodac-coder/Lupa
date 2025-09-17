# store/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import decimal
from django.core.validators import MinValueValidator, MaxValueValidator

class CustomUser(AbstractUser):
    cpf = models.CharField(max_length=14, unique=True, help_text="Formato: 123.456.789-10")
    groups = models.ManyToManyField(
        Group, verbose_name='groups', blank=True, related_name="customuser_set"
    )
    user_permissions = models.ManyToManyField(
        Permission, verbose_name='user permissions', blank=True, related_name="customuser_set"
    )
    def __str__(self):
        return self.username

# --- VERSÃO ÚNICA E CORRIGIDA DO MODELO PRODUCT ---
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    has_capacity_options = models.BooleanField(
        "Habilitar opções de capacidade?",
        default=True,
        help_text="Marque esta opção se este produto tiver opções de capacidade (ex: 128GB, 256GB)."
    )
    def __str__(self):
        return self.name
    
    def get_installment_value(self, installments=12):
        if installments > 0:
            return self.price / decimal.Decimal(installments)
        return self.price

class ColorVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, help_text="Ex: Preto, Verde-acinzentado")
    color_code = models.CharField(max_length=7, help_text="Código Hexadecimal da cor, ex: #000000")

    def __str__(self):
        return f"{self.product.name} ({self.name})"

class VariantImage(models.Model):
    variant = models.ForeignKey(ColorVariant, related_name='images', on_delete=models.CASCADE)
    # Garanta que o 'upload_to' esteja correto
    image = models.ImageField(upload_to='variant_images/')

    def __str__(self):
        return f"Imagem para {self.variant.name}"
class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=10)
    complement = models.CharField(max_length=100, blank=True, null=True)
    neighborhood = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=9)

    def __str__(self):
        return f"{self.street}, {self.number} - {self.city}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('AWAITING_PAYMENT', 'Aguardando Pagamento'),
        ('PROCESSING', 'Processando'),
        ('COMPLETED', 'Concluído'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AWAITING_PAYMENT')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.product.name}"
    
class ContactMessage(models.Model):
    name = models.CharField("Nome", max_length=100)
    email = models.EmailField("E-mail")
    subject = models.CharField("Assunto", max_length=200)
    message = models.TextField("Mensagem")
    created_at = models.DateTimeField("Enviado em", auto_now_add=True)

    def __str__(self):
        return self.subject
    
class Coupon(models.Model):
    code = models.CharField("Código", max_length=50, unique=True)
    discount_percent = models.DecimalField(
        "Porcentagem de Desconto",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    active = models.BooleanField("Ativo", default=True)
    valid_from = models.DateTimeField("Válido de")
    valid_to = models.DateTimeField("Válido até")

    def __str__(self):
        return self.code
    
