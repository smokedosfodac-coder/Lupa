from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

# --- 1. USUÁRIO E ENDEREÇO ---

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=200, verbose_name="Rua")
    number = models.CharField(max_length=20, verbose_name="Número")
    neighborhood = models.CharField(max_length=100, verbose_name="Bairro")
    city = models.CharField(max_length=100, verbose_name="Cidade")
    state = models.CharField(max_length=2, verbose_name="Estado")
    zip_code = models.CharField(max_length=9, verbose_name="CEP")

    def __str__(self):
        return f"{self.street}, {self.number}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome")
    email = models.EmailField(verbose_name="E-mail")
    subject = models.CharField(max_length=200, verbose_name="Assunto")
    message = models.TextField(verbose_name="Mensagem")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject

# --- 2. CATÁLOGO (Produtos, Lentes e Variações) ---

class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    def __str__(self): return self.name

class RubberColor(models.Model):
    name = models.CharField(max_length=50, verbose_name="Nome da Cor")
    color_code = models.CharField(max_length=7, verbose_name="Cor Hex")
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class LensType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Tipo da Lente")
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    is_promo_buy_1_get_2 = models.BooleanField(default=False, verbose_name="Promoção: Compre 1 Leve 2?")
    available_rubbers = models.ManyToManyField(RubberColor, blank=True)

    def get_parcela_10x(self):
        return self.price / 10
    
    def save(self, *args, **kwargs):
        # Lógica automática apenas se categoria estiver vazia
        if not self.category:
            nome_produto = self.name.lower()
            slug_destino = None
            if 'oakley' in nome_produto: slug_destino = 'oakley'
            elif 'grau' in nome_produto: slug_destino = 'grau'
            elif 'solar' in nome_produto or 'sol' in nome_produto: slug_destino = 'solar'
            elif 'acessorio' in nome_produto: slug_destino = 'acessorios'
            
            if slug_destino:
                try:
                    self.category = Category.objects.get(slug=slug_destino)
                except Category.DoesNotExist:
                    pass
        super().save(*args, **kwargs)

    def __str__(self): return self.name

class ProductLensImage(models.Model):
    product = models.ForeignKey(Product, related_name='lens_images', on_delete=models.CASCADE)
    lens = models.ForeignKey(LensType, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/lenses/')
    class Meta:
        unique_together = ('product', 'lens')

# --- 3. MODELOS DE PEDIDOS (Sistema de Vendas) ---

STATUS_CHOICES = (
    ('pendente', 'Aguardando Pagamento'),
    ('pago', 'Pagamento Concluído'),
    ('preparando', 'Aguardando Envio'),
    ('enviado', 'Enviado'),
    ('entregue', 'Entregue'),
    ('cancelado', 'Cancelado'),
)

class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=100, verbose_name="Nome Completo")
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(verbose_name="Endereço de Entrega")
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    tracking_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código de Rastreio")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200) # Backup do nome
    lens_name = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def get_subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

# --- 4. SISTEMA DE EMAIL AUTOMÁTICO ---

@receiver(post_save, sender=Order)
def send_order_emails(sender, instance, created, **kwargs):
    SENDER_EMAIL = 'exemplo@exemplo.com'
    ADMIN_EMAIL = 'gabrielferreira2840@gmail.com'

    if created:
        # Email para o Cliente
        subject_client = f'Pedido #{instance.id} Recebido!'
        message_client = f"Olá {instance.full_name},\n\nSeu pedido #{instance.id} foi recebido.\nStatus: {instance.get_status_display()}\nValor: R$ {instance.total_price}"
        send_mail(subject_client, message_client, SENDER_EMAIL, [instance.email], fail_silently=True)

        # Email para o Dono
        subject_admin = f'Nova Venda! Pedido #{instance.id}'
        message_admin = f"Nova venda realizada!\nCliente: {instance.full_name}\nTotal: R$ {instance.total_price}"
        send_mail(subject_admin, message_admin, SENDER_EMAIL, [ADMIN_EMAIL], fail_silently=True)

    else:
        # Email de Atualização (Status ou Rastreio)
        subject_update = f'Atualização do Pedido #{instance.id}'
        message_update = f"O status do seu pedido mudou para: {instance.get_status_display()}."
        
        if instance.status == 'enviado' and instance.tracking_code:
            message_update += f"\n\nCódigo de Rastreio: {instance.tracking_code}"
            
        send_mail(subject_update, message_update, SENDER_EMAIL, [instance.email], fail_silently=True)