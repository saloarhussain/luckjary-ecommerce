from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('cart/remove-coupon/', views.remove_coupon, name='remove_coupon'),

    # Checkout & Success
    path('checkout/', views.checkout, name='checkout'),
    path('order/confirmed/<str:order_number>/', views.order_success, name='order_success'),
    path('order/view/<str:order_number>/', views.order_detail, name='order_detail'),

    # Real-Time Customer Tracking Portal
    path('track/', views.order_tracking, name='order_tracking'),
    path('track/<str:order_number>/', views.order_tracking, name='order_tracking_direct'),

    # Admin OMS Centralized Dashboard
    path('oms/', views.oms_dashboard, name='oms_dashboard'),
]
