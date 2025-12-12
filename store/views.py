from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.db.models import Q
from .models import Product, Category, ContactMessage
from .forms import CustomUserCreationForm, ContactForm, AddressForm
from .models import LensType
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem # Importe LensType aqui
from .forms import UserUpdateForm # Importe o form novo
import mercadopago
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
# --- VIEWS DE PRODUTOS ---
# Em store/views.py

def product_list(request):
    # Filtra os produtos pelo Slug da categoria
    # Se a categoria não existir ou não tiver produtos, a lista fica vazia
    oakley = Product.objects.filter(category__slug='oakley')
    solar = Product.objects.filter(category__slug='solar')
    grau = Product.objects.filter(category__slug='grau')
    acessorios = Product.objects.filter(category__slug='acessorios')

    context = {
        'oakley': oakley,
        'solar': solar,
        'grau': grau,
        'acessorios': acessorios,
    }
    
    # Vamos renderizar um template específico para a Home, não o base direto
    return render(request, 'home.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'product_detail.html', {'product': product})

def category_view(request, category_name):
    category = Category.objects.filter(slug=category_name).first()
    if not category:
        category = Category.objects.filter(name__iexact=category_name).first()
    
    products = Product.objects.filter(category=category) if category else []
    return render(request, 'category_list.html', {'products': products, 'category_name': category_name})

def promo_view(request):
    products = Product.objects.filter(is_promo_buy_1_get_2=True)
    return render(request, 'category_list.html', {'products': products, 'category_name': 'Promoção: Compre 1 Leve 2 🔥'})

def search_view(request):
    query = request.GET.get('q')
    products = []
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    return render(request, 'search_results.html', {'products': products, 'query': query})

# --- SISTEMA DE CARRINHO (NOVO) ---

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    lens_id = request.POST.get('lens_id')
    
    # --- VALIDAÇÃO NO SERVIDOR ---
    # Se o produto tem lentes cadastradas, mas nenhuma foi escolhida
    if product.lens_images.exists() and not lens_id:
        # Você pode usar messages para mostrar erro ou apenas redirecionar
        return redirect('product_detail', slug=product.slug)

    # Cria a chave do carrinho
    cart_key = f"{product_id}-{lens_id}"
    
    cart = request.session.get('cart', {})
    cart[cart_key] = cart.get(cart_key, 0) + 1
    request.session['cart'] = cart
    
    return redirect('cart_view')

def update_cart(request, cart_key, action):
    cart = request.session.get('cart', {})
    
    if cart_key in cart:
        if action == 'increase':
            cart[cart_key] += 1
        elif action == 'decrease':
            cart[cart_key] -= 1
            if cart[cart_key] <= 0:
                del cart[cart_key]
    
    request.session['cart'] = cart
    return redirect('cart_view')

def remove_from_cart(request, cart_key):
    cart = request.session.get('cart', {})
    if cart_key in cart:
        del cart[cart_key]
        request.session['cart'] = cart
    return redirect('cart_view')

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    promo_items = [] 

    for cart_key, quantity in cart.items():
        # Separa a chave "15-3" em Product ID e Lens ID
        try:
            p_id, l_id = cart_key.split('-')
            product = Product.objects.get(id=p_id)
            
            # Tenta buscar o nome da lente
            lens_name = "Padrão"
            lens_image = product.image.url if product.image else None
            
            if l_id and l_id != 'None' and l_id != '':
                try:
                    lens_obj = LensType.objects.get(id=l_id)
                    lens_name = lens_obj.name
                    # Tenta pegar a foto específica dessa lente
                    lens_variation = product.lens_images.filter(lens=lens_obj).first()
                    if lens_variation:
                        lens_image = lens_variation.image.url
                except LensType.DoesNotExist:
                    pass

            subtotal = product.price * quantity
            total_price += subtotal
            
            item = {
                'key': cart_key, # Chave usada para remover/atualizar
                'product': product,
                'lens_name': lens_name,
                'image_url': lens_image,
                'quantity': quantity,
                'subtotal': subtotal
            }
            cart_items.append(item)

            if product.is_promo_buy_1_get_2:
                for _ in range(quantity):
                    promo_items.append(product.price)
        except:
            continue # Ignora itens com erro no carrinho antigo

    # Lógica de Desconto (Igual anterior)
    discount = 0
    promo_count = len(promo_items)
    if promo_count >= 2:
        promo_items.sort()
        items_to_discount = promo_count // 2 
        for i in range(items_to_discount):
            discount += promo_items[i]

    final_price = total_price - discount

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'discount': discount,
        'final_price': final_price,
        'promo_active': discount > 0
    })

    # 2. LÓGICA COMPRE 1 LEVE 2 (Desconto Automático)
    discount = 0
    promo_count = len(promo_items)
    
    if promo_count >= 2:
        # Ordena os preços do menor para o maior
        promo_items.sort()
        # A cada par, o mais barato sai de graça.
        # Ex: Se tem 2 itens, 1 é desconto. Se tem 4 itens, 2 são desconto.
        items_to_discount = promo_count // 2 
        
        # Soma os preços dos itens mais baratos para dar o desconto
        for i in range(items_to_discount):
            discount += promo_items[i]

    final_price = total_price - discount

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'discount': discount,
        'final_price': final_price,
        'promo_active': discount > 0
    })

# --- VIEWS UTILITÁRIAS ---
def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'contact_success.html')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def register_or_login(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # 1. Salva o usuário
            user = form.save()
            
            # 2. Faz o Login Automático
            # Especificamos o backend para evitar aquele erro de "Multiple backends"
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # 3. Redireciona para a loja
            return redirect('product_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('product_list')

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            # 1. Salva endereço no usuário
            dados = form.cleaned_data
            user = request.user
            user.rua = dados['rua']
            user.numero = dados['numero']
            user.complemento = dados['complemento']
            user.bairro = dados['bairro']
            user.cidade = dados['cidade']
            user.estado = dados['estado']
            user.cep = dados['cep']
            user.save()

            endereco_completo = f"{dados['rua']}, {dados['numero']} - {dados['bairro']}, {dados['cidade']}/{dados['estado']} - CEP: {dados['cep']}"
            if dados['complemento']:
                endereco_completo += f" ({dados['complemento']})"

            # 2. Calcula Totais
            total_price = 0
            promo_items = []
            final_items = []

            for key, qtd in cart.items():
                try:
                    p_id, l_id = key.split('-')
                    product = Product.objects.get(id=p_id)
                    lens_name = "Padrão"
                    if l_id and l_id != 'None':
                        try: lens_name = LensType.objects.get(id=l_id).name
                        except: pass
                    
                    total_price += product.price * qtd
                    final_items.append({'product': product, 'qty': qtd, 'price': product.price, 'lens': lens_name})
                    if product.is_promo_buy_1_get_2:
                        for _ in range(qtd): promo_items.append(product.price)
                except: pass

            discount = 0
            if len(promo_items) >= 2:
                promo_items.sort()
                for i in range(len(promo_items) // 2): discount += promo_items[i]
            
            final_total = total_price - discount

            # 3. Cria o Pedido
            order = Order.objects.create(
                user=request.user,
                full_name=f"{request.user.first_name} {request.user.last_name}",
                email=request.user.email,
                phone=request.user.phone or "",
                address=endereco_completo,
                total_price=final_total,
                status='pendente'
            )

            for item in final_items:
                OrderItem.objects.create(
                    order=order, product=item['product'], product_name=item['product'].name,
                    lens_name=item['lens'], price=item['price'], quantity=item['qty']
                )

            request.session['cart'] = {}

            # --- AQUI MUDOU: SEM IF/ELSE, VAI DIRETO PRO MERCADO PAGO ---
            try:
                # Manda todo mundo para o link do Checkout Pro (Lá eles escolhem Pix ou Cartão)
                payment_url = gerar_link_pagamento(order)
                return redirect(payment_url)
            except Exception as e:
                print(f"Erro MP: {e}")
                return redirect('order_detail', order_id=order.id)
            # ------------------------------------------------------------
    
    else:
        # GET: Preenche formulário
        initial_data = {
            'rua': request.user.rua,
            'numero': request.user.numero,
            'complemento': request.user.complemento,
            'bairro': request.user.bairro,
            'cidade': request.user.cidade,
            'estado': request.user.estado,
            'cep': request.user.cep,
        }
        form = AddressForm(initial=initial_data)

    return render(request, 'checkout.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            dados = form.cleaned_data
            user = request.user
            user.rua = dados['rua']
            user.numero = dados['numero']
            user.complemento = dados['complemento']
            user.bairro = dados['bairro']
            user.cidade = dados['cidade']
            user.estado = dados['estado']
            user.cep = dados['cep']
            user.save()
            # Adiciona uma mensagem de sucesso (opcional, mas bom)
            return redirect('profile')
    else:
        initial_data = {
            'rua': request.user.rua,
            'numero': request.user.numero,
            'complemento': request.user.complemento,
            'bairro': request.user.bairro,
            'cidade': request.user.cidade,
            'estado': request.user.estado,
            'cep': request.user.cep,
        }
        form = AddressForm(initial=initial_data)
    
    # Busca os pedidos do usuário para mostrar também
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'profile.html', {'form': form, 'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_detail.html', {'order': order})

def logout_view(request):
    logout(request)
    return redirect('product_list')

import mercadopago


@csrf_exempt
@require_POST
def mp_webhook(request):
    topic = request.GET.get("topic") or request.GET.get("type")
    resource_id = request.GET.get("id") or request.GET.get("data.id")

    if topic == "payment":
        sdk = mercadopago.SDK("SEU_ACCESS_TOKEN_DE_PRODUCAO_AQUI") # Token PROD
        
        payment_info = sdk.payment().get(resource_id)
        payment = payment_info["response"]
        
        order_id = payment["external_reference"]
        status = payment["status"]

        try:
            order = Order.objects.get(id=order_id)
            
            # Só envia email se o pedido mudar de 'pendente' para 'pago'
            # (Isso evita enviar email duplo se o MP avisar duas vezes)
            if status == "approved" and order.status != 'pago':
                order.status = "pago"
                order.save()
                
                # --- 1. MONTA O EMAIL PARA VOCÊ (ADMIN) ---
                itens_texto = ""
                for item in order.items.all():
                    itens_texto += f"- {item.product.name} ({item.lens_name}) | Qtd: {item.quantity}\n"

                msg_admin = f"""
                🚀 NOVA VENDA APROVADA! (#{order.id})

                COMPRADOR:
                Nome: {order.full_name}
                Email: {order.email}
                Telefone: {order.phone}

                ENTREGA:
                {order.address}

                ITENS VENDIDOS:
                {itens_texto}

                VALOR TOTAL: R$ {order.total_price}
                
                Corre separar o pedido! 🏃‍♂️
                """

                try:
                    send_mail(
                        subject=f"Nova Venda! Pedido #{order.id}",
                        message=msg_admin,
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=['gabrielferreira2840@gmail.com'], # Para onde vai
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Erro ao enviar email admin: {e}")

                # --- 2. MONTA O EMAIL PARA O CLIENTE ---
                msg_cliente = f"""
                Olá, {order.full_name.split()[0]}! 👋

                Seu pagamento foi confirmado com sucesso!
                Obrigado por comprar na nossa loja.

                Seu pedido #{order.id} já está sendo separado com carinho.
                
                Detalhes da entrega:
                {order.address}

                Qualquer dúvida, responda este email.
                """

                try:
                    send_mail(
                        subject=f"Pedido #{order.id} Confirmado! 🎉",
                        message=msg_cliente,
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[order.email], # Para o email do cliente
                        fail_silently=True,
                    )
                except:
                    pass # Se der erro no email do cliente, não faz mal, o pedido já tá pago

                print(f"PEDIDO {order_id} PAGO E EMAILS ENVIADOS!")
                
            elif status == "failure" or status == "cancelled":
                order.status = "cancelado"
                order.save()
                
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)