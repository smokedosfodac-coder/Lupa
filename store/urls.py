from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('produto/<slug:slug>/', views.product_detail, name='product_detail'),
    path('categoria/<str:category_name>/', views.category_view, name='category_view'),
    path('busca/', views.search_view, name='search_view'),
    path('contato/', views.contact_view, name='contact_view'),
    
    # Autenticação
    path('cadastro/', views.register_or_login, name='register_or_login'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('promocao-especial/', views.promo_view, name='promo_view'), # <--- Nova linha

    path('carrinho/', views.cart_view, name='cart_view'),
    path('adicionar/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('atualizar/<str:cart_key>/<str:action>/', views.update_cart, name='update_cart'),
    path('remover/<str:cart_key>/', views.remove_from_cart, name='remove_from_cart'),
    path('finalizar-compra/', views.checkout_view, name='checkout'),
    path('minha-conta/', views.profile_view, name='profile_view'),
    path('pedido/<int:order_id>/', views.order_detail, name='order_detail'),
    # Adicione na lista de urlpatterns
    path('minha-conta/', views.profile_view, name='profile'),
    path('pagamento/pix/<int:order_id>/', views.pagamento_pix_view, name='pagamento_pix'),
]

