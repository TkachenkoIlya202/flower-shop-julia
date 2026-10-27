from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.catalog_view, name='catalog'),
    path('category/<slug:category_slug>/', views.catalog_view, name='catalog_by_category'),
    path('product/<int:id>/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('cart/', views.cart_detail_view, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add_view, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove_view, name='cart_remove'),
    path('cart/update/<int:product_id>/', views.cart_update_view, name='cart_update'),
    path('cart/api/', views.cart_api_view, name='cart_api'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success_view, name='order_success'),
]
