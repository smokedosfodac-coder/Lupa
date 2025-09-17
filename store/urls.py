# store/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.product_list, name='product_list'), 
    path('buscar/', views.search_view, name='search_view'),
    path('categoria/<slug:category_name>/', views.category_view, name='category_view'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('produto/<int:product_id>/', views.product_page, name='product_page'),
    path('iniciar-compra/', views.start_purchase, name='start_purchase'),
    path('carrinho/', views.cart_view, name='cart_view'),
    path('prosseguir-checkout/', views.proceed_to_checkout, name='proceed_to_checkout'),
    path('cadastro/', views.register_view, name='register_or_login'), # Simplificado para ir direto ao cadastro
    path('contato/', views.contact_view, name='contact_view'),
    # Checkout
    path('checkout/endereco/', views.checkout_address, name='checkout_address'),
    path('checkout/frete/', views.checkout_shipping, name='checkout_shipping'),
    path('checkout/pagamento/', views.checkout_payment, name='checkout_payment'),
    path('checkout/concluido/', views.checkout_confirmation, name='checkout_confirmation'),
    path('checkout/falha/', views.payment_failure, name='payment_failure'),
]