from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
import mercadopago
from django.db.models import Q
from .forms import ContactForm
from .forms import CustomUserCreationForm, AddressForm
from .models import Order, Product, ColorVariant, Coupon
from django.utils import timezone 
from django.contrib import messages 
from django.db.models import Case, When, Value, IntegerField



def product_list(request):
    # Busca os produtos para cada categoria separadamente
    iphones_17 = Product.objects.filter(name__icontains='iPhone 17').annotate(
        custom_order=Case(
            # A ordem dos When é importante. Primeiro o mais específico.
            When(name__icontains='Pro Max', then=Value(0)),
            When(name__icontains='Pro', then=Value(1)),
            When(name__icontains='Air', then=Value(3)),
            default=Value(2), # O que sobrar (modelo normal) fica com a prioridade 2
            output_field=IntegerField(),
        )
    ).order_by('custom_order').prefetch_related('variants__images')
    iphones_16 = Product.objects.filter(name__icontains='iPhone 16').prefetch_related('variants__images')
    macs = Product.objects.filter(name__icontains='Mac').prefetch_related('variants__images')
    airpods = Product.objects.filter(name__icontains='AirPods').prefetch_related('variants__images')
    apple_watches = Product.objects.filter(name__icontains='Apple Watch').prefetch_related('variants__images')

    context = {
        'iphones_17': iphones_17,
        'iphones_16': iphones_16,
        'macs': macs,
        'airpods': airpods,
        'apple_watches': apple_watches,
    }
    return render(request, 'store/product_list.html', context)

def product_page(request, product_id):
    product = get_object_or_404(
        Product.objects.prefetch_related("variants__images"),
        id=product_id
    )
    return render(request, 'store/product_page.html', {"product": product})

def start_purchase(request):
    if request.method == 'POST':
        purchase_info = {
            'product_id': request.POST.get('product_id'),
            'variant_id': request.POST.get('variant_id'),
            'capacity': request.POST.get('capacity'),
            'quantity': 1,
        }
        request.session['purchase_info'] = purchase_info
        request.session.pop('shipping_cost', None)
        request.session.pop('discount_amount', None)
        return redirect('cart_view')
    return redirect('product_list')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('checkout_address')
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/register.html', {'form': form})

# store/views.py
def cart_view(request):
    purchase_info = request.session.get('purchase_info')
    if not purchase_info:
        return redirect('product_list')

    product = get_object_or_404(Product, id=purchase_info.get('product_id'))
    selected_variant = get_object_or_404(ColorVariant, id=purchase_info.get('variant_id'))
    
    # ... (cálculo de subtotal com base na capacidade) ...
    base_price = product.price
    selected_capacity = purchase_info.get('capacity')
    price_increase = Decimal('0.00')
    if selected_capacity == '256GB': price_increase = Decimal('400.00')
    elif selected_capacity == '512GB': price_increase = Decimal('800.00')
    subtotal = base_price + price_increase

    cart_image_url = selected_variant.images.first().image.url if selected_variant.images.exists() else None
    
    # Inicializa variáveis
    shipping_cost = request.session.get('shipping_cost')
    coupon_id = request.session.get('coupon_id')
    discount_amount = Decimal('0.00')

    # Se um cupom já foi aplicado, recalcula o desconto
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            discount_amount = (subtotal * coupon.discount_percent) / 100
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'calculate_shipping':
            shipping_cost = str(Decimal('50.00') if subtotal < 1500 else Decimal('0.00'))
            request.session['shipping_cost'] = shipping_cost

        elif action == 'apply_coupon':
            coupon_code = request.POST.get('coupon_code', '').strip().upper()
            now = timezone.now()
            try:
                # Busca o cupom no banco de dados
                coupon = Coupon.objects.get(
                    code__iexact=coupon_code,
                    active=True,
                    valid_from__lte=now,
                    valid_to__gte=now
                )
                # Calcula o desconto
                discount_amount = (subtotal * coupon.discount_percent) / 100
                request.session['coupon_id'] = coupon.id # Salva o ID do cupom na sessão
                messages.success(request, f"Cupom '{coupon.code}' aplicado com sucesso!")
            except Coupon.DoesNotExist:
                request.session['coupon_id'] = None
                messages.error(request, "Este cupom é inválido ou expirou.")
    
    # Converte para Decimal para o cálculo final
    shipping_cost_decimal = Decimal(shipping_cost) if shipping_cost is not None else None
    total = subtotal - discount_amount
    if shipping_cost_decimal is not None:
        total += shipping_cost_decimal
    
    context = {
        'product': product,
        'selected_variant': selected_variant,
        'capacity': purchase_info.get('capacity'),
        'cart_image_url': cart_image_url,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost_decimal,
        'discount_amount': discount_amount,
        'total': total
    }
    return render(request, 'store/cart.html', context)

def proceed_to_checkout(request):
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={reverse('checkout_address')}")
    return redirect('checkout_address')

# store/views.py

@login_required
def checkout_address(request):
    """ ETAPA 1: Coleta o endereço do usuário. """
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            # Salva o endereço no banco de dados
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            
            # Guarda o ID do endereço na sessão para o próximo passo
            request.session['address_id'] = address.id
            
            # Redireciona para a nova etapa de seleção de frete
            return redirect('checkout_shipping')
    else:
        form = AddressForm()

    return render(request, 'store/checkout_address.html', {'form': form})


@login_required
def checkout_shipping(request):
    """ ETAPA 2: Mostra as opções de frete e cria a Ordem. """
    # Se o usuário confirmar o frete (método POST)
    if request.method == 'POST':
        purchase_info = request.session.get('purchase_info')
        address_id = request.session.get('address_id')

        # Segurança: Garante que temos todas as informações
        if not purchase_info or not address_id:
            return redirect('cart_view')

        # Cria a Ordem no banco de dados com todas as informações coletadas
        order = Order.objects.create(
            user=request.user,
            product_id=purchase_info['product_id'],
            quantity=purchase_info.get('quantity', 1),
            shipping_address_id=address_id,
            status='AWAITING_PAYMENT'
        )
        
        # Salva o ID da ordem na sessão para o pagamento
        request.session['order_id'] = order.id
        
        # Redireciona para a etapa final: o pagamento
        return redirect('checkout_payment')

    # Se for um GET, apenas mostra a página de seleção de frete
    return render(request, 'store/checkout_shipping.html')


@login_required
def checkout_payment(request):
    """ ETAPA 3: Integra com o Mercado Pago. """
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('cart_view')
    
    order = get_object_or_404(Order, id=order_id)
    
    # Lógica para calcular o preço final com base na capacidade
    purchase_info = request.session.get('purchase_info', {})
    selected_capacity = purchase_info.get('capacity')
    base_price = order.product.price
    price_increase = Decimal('0.00')
    if selected_capacity == '256GB':
        price_increase = Decimal('400.00')
    elif selected_capacity == '512GB':
        price_increase = Decimal('800.00')
    
    final_price = base_price + price_increase

    # Configuração do Mercado Pago
    sdk = mercadopago.SDK("SEU_ACCESS_TOKEN") # Lembre-se de usar seu token

    preference_data = {
        "items": [{
            "title": f"{order.product.name} ({purchase_info.get('capacity')})",
            "quantity": order.quantity,
            "unit_price": float(final_price)
        }],
        "back_urls": {
            "success": request.build_absolute_uri(reverse('checkout_confirmation')),
            "failure": request.build_absolute_uri(reverse('payment_failure')),
        },
        "auto_return": "approved",
        "external_reference": order.id,
    }
    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]
    
    context = {
        'preference_id': preference['id'],
        'mercado_pago_public_key': "SUA_PUBLIC_KEY" # Lembre-se de usar sua chave
    }
    return render(request, 'store/checkout_payment.html', context)


@login_required
def checkout_confirmation(request):
    # O Mercado Pago adiciona parâmetros na URL, podemos usá-los para verificar
    payment_status = request.GET.get('status')
    order_id = request.GET.get('external_reference')

    if payment_status == 'approved':
        order = Order.objects.get(id=order_id)
        order.status = 'COMPLETED' # Atualiza o status do pedido
        order.save()

        # Limpa a sessão
        del request.session['purchase_info']
        del request.session['order_id']
        
        return render(request, 'store/checkout_confirmation.html', {'order': order})
    else:
        # Se o pagamento falhar ou for pendente
        return redirect('payment_failure')

def payment_failure(request):
    return render(request, 'store/payment_failure.html') # Crie este template


# store/views.py

def category_view(request, category_name):
    print(f"\n--- DEBUG: Categoria recebida da URL: '{category_name}' ---")

    category_keywords = {
        'iphone': 'iPhone',
        'mac': 'Mac',
        'ipad': 'iPad',
        'apple-watch': 'Apple Watch',
        'airpods': 'AirPods',
    }
    
    keyword = category_keywords.get(category_name)
    print(f"[DEBUG] Palavra-chave de busca usada: '{keyword}'")

    if keyword:
        products = Product.objects.filter(name__icontains=keyword).prefetch_related('variants__images')
        print(f"[DEBUG] Produtos encontrados com essa palavra-chave: {products.count()}")
        page_title = keyword
    else:
        products = []
        page_title = "Categoria não encontrada"
        print("[DEBUG] Nenhuma palavra-chave correspondente encontrada.")

    print("--- FIM DO DEBUG ---\n")
    
    context = {
        'products': products,
        'page_title': page_title
    }
    return render(request, 'store/product_list.html', context)

# View para a busca
def search_view(request):
    query = request.GET.get('q') # Pega o que o usuário digitou
    if query:
        # Exemplo de busca simples por nome
        products = Product.objects.filter(name__icontains=query).prefetch_related('variants__images')
        page_title = f"Resultados para: {query}"
    else:
        products = []
        page_title = "Por favor, digite um termo de busca"

    context = {
        'products': products,
        'page_title': page_title
    }
    return render(request, 'store/product_list.html', context)

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            # Adiciona uma mensagem de sucesso
            messages.success(request, 'Sua mensagem foi enviada com sucesso! Responderemos em breve.')
            return redirect('contact_view') # Redireciona para a mesma página (limpa)
    else:
        form = ContactForm()
    
    return render(request, 'store/contact.html', {'form': form})