from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from catalog.models import Product
from accounts.models import Address, CustomUser
from .models import Order, OrderItem, OrderStatusUpdate, Coupon
import datetime

# --- Shopping Cart Views ---

def cart_view(request):
    return render(request, 'orders/cart.html', {
        'meta_title': 'Shopping Bag | Luckjary Fine Jewelry',
        'meta_description': 'Review your selected haute joaillerie pieces, calculate insured shipping, and proceed to checkout.',
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = request.session.get('cart', {})
    
    qty = int(request.POST.get('quantity', 1))
    size = request.POST.get('size', 'Standard / US 7')
    material = request.POST.get('material', product.karat_metal)

    pid_str = str(product_id)
    if pid_str in cart:
        cart[pid_str]['quantity'] += qty
        cart[pid_str]['size'] = size
        cart[pid_str]['material'] = material
    else:
        cart[pid_str] = {
            'quantity': qty,
            'size': size,
            'material': material,
        }

    request.session['cart'] = cart
    request.session.modified = True

    msg = f"Added {qty}x {product.title} to your shopping bag."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': msg, 'cart_count': sum(item['quantity'] for item in cart.values())})

    messages.success(request, msg)
    return redirect('orders:cart')

def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    pid_str = str(product_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if pid_str in cart:
            if action == 'increase':
                cart[pid_str]['quantity'] += 1
            elif action == 'decrease':
                cart[pid_str]['quantity'] -= 1
                if cart[pid_str]['quantity'] <= 0:
                    del cart[pid_str]
            elif action == 'remove':
                del cart[pid_str]

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('orders:cart')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    pid_str = str(product_id)
    if pid_str in cart:
        del cart[pid_str]
        request.session['cart'] = cart
        request.session.modified = True
        messages.info(request, "Item removed from shopping bag.")
    return redirect('orders:cart')

def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        try:
            coupon = Coupon.objects.get(code=code, active=True)
            request.session['coupon_code'] = coupon.code
            request.session['coupon_discount_percent'] = coupon.discount_percent if coupon.is_percent else 0
            request.session['coupon_discount_amount'] = float(coupon.discount_amount) if not coupon.is_percent else 0
            messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid or expired promotional code.")
    return redirect('orders:cart')

def remove_coupon(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
    if 'coupon_discount_percent' in request.session:
        del request.session['coupon_discount_percent']
    if 'coupon_discount_amount' in request.session:
        del request.session['coupon_discount_amount']
    request.session.modified = True
    messages.info(request, "Promotional code removed.")
    return redirect('orders:cart')


# --- Checkout Views ---

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Your shopping bag is empty.")
        return redirect('catalog:product_list')

    # Saved addresses for logged-in user
    if request.user.is_authenticated:
        saved_addresses = Address.objects.filter(user=request.user)
        default_address = saved_addresses.filter(is_default=True).first() or saved_addresses.first()
    else:
        saved_addresses = Address.objects.none()
        default_address = None

    if request.method == 'POST':
        # Retrieve customer contact
        if request.user.is_authenticated:
            email = request.user.email
            full_name = request.POST.get('full_name') or request.user.get_full_name() or request.user.username
            phone = request.POST.get('phone') or request.user.phone_number or ''
        else:
            email = request.POST.get('email', '').strip().lower()
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()

        # Shipping Address
        street = request.POST.get('street_address', '').strip()
        apt = request.POST.get('apartment_suite', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state_province', '').strip()
        zip_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', 'United States').strip()
        
        gift_wrapping = request.POST.get('gift_wrapping') == 'on'
        gift_message = request.POST.get('gift_message', '').strip()
        payment_method = request.POST.get('payment_method', 'Credit Card (Stripe Encrypted)')

        if not email or not full_name or not street or not city or not state or not zip_code:
            messages.error(request, "Please fill in all required shipping and contact details.")
            return render(request, 'orders/checkout.html', {
                'saved_addresses': saved_addresses,
                'default_address': default_address,
            })

        # Calculate Totals
        product_ids = [int(pid) for pid in cart.keys() if pid.isdigit()]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        
        subtotal = 0.00
        order_items_to_create = []

        for pid_str, item_info in cart.items():
            if not pid_str.isdigit():
                continue
            p = products.get(int(pid_str))
            if p:
                qty = item_info.get('quantity', 1)
                unit_price = float(p.price)
                line_total = unit_price * qty
                subtotal += line_total
                order_items_to_create.append({
                    'product': p,
                    'name': p.title,
                    'sku': p.sku,
                    'image': p.primary_image,
                    'size': item_info.get('size', 'Standard / US 7'),
                    'material': item_info.get('material', p.karat_metal),
                    'unit_price': unit_price,
                    'qty': qty,
                })
                # Decrement inventory
                p.inventory = max(0, p.inventory - qty)
                p.save(update_fields=['inventory'])

        # Discounts
        coupon_obj = None
        discount_amount = 0.00
        coupon_code = request.session.get('coupon_code')
        if coupon_code:
            try:
                coupon_obj = Coupon.objects.get(code=coupon_code, active=True)
                if coupon_obj.is_percent:
                    discount_amount = round((subtotal * coupon_obj.discount_percent) / 100.0, 2)
                else:
                    discount_amount = min(subtotal, float(coupon_obj.discount_amount))
            except Coupon.DoesNotExist:
                pass

        total_amount = max(0.00, subtotal - discount_amount)

        # Create Order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            email=email,
            full_name=full_name,
            phone=phone,
            shipping_street=street,
            shipping_apartment=apt,
            shipping_city=city,
            shipping_state=state,
            shipping_zip=zip_code,
            shipping_country=country,
            status='PENDING',
            payment_status='PAID',
            payment_method=payment_method,
            carrier='FedEx Luxury Priority Overnight',
            subtotal=subtotal,
            shipping_cost=0.00, # Complimentary luxury shipping
            discount_amount=discount_amount,
            total_amount=total_amount,
            coupon=coupon_obj,
            gift_wrapping=gift_wrapping,
            gift_message=gift_message,
        )

        for item_data in order_items_to_create:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                product_name=item_data['name'],
                product_sku=item_data['sku'],
                product_image=item_data['image'],
                selected_size=item_data['size'],
                selected_material=item_data['material'],
                unit_price=item_data['unit_price'],
                quantity=item_data['qty']
            )

        # Create Initial Order Status Milestone
        OrderStatusUpdate.objects.create(
            order=order,
            status='PENDING',
            title='Order Confirmed & Security Verified',
            description='Payment successfully authorized via encrypted gateway. Order logged into atelier schedule.',
            location='Luckjary Security & Vault, New York, NY'
        )

        # Clear cart and coupon from session
        request.session['cart'] = {}
        if 'coupon_code' in request.session:
            del request.session['coupon_code']
        request.session.modified = True

        return redirect('orders:order_success', order_number=order.order_number)

    return render(request, 'orders/checkout.html', {
        'saved_addresses': saved_addresses,
        'default_address': default_address,
        'meta_title': 'Express Luxury Checkout | Luckjary',
    })

def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    is_guest = order.user is None
    return render(request, 'orders/order_success.html', {
        'order': order,
        'is_guest': is_guest,
        'meta_title': f"Order Confirmed #{order.order_number} | Luckjary",
    })

def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    # Check permissions if user is logged in
    if order.user and request.user.is_authenticated and order.user != request.user and not request.user.is_staff:
        messages.error(request, "You are not authorized to view this order.")
        return redirect('accounts:profile')

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'meta_title': f"Order #{order.order_number} Details | Luckjary",
    })


# --- Customer Real-Time Order Tracking Portal ---

def order_tracking(request, order_number=None):
    order = None
    searched = False
    error_msg = None
    input_order_number = order_number or ''
    input_email = ''

    if order_number:
        try:
            order = Order.objects.get(order_number=order_number)
            searched = True
            input_order_number = order_number
            input_email = order.email
        except Order.DoesNotExist:
            error_msg = f"Order #{order_number} could not be located."
    elif request.method == 'POST' or request.GET.get('order_number'):
        num = (request.POST.get('order_number') or request.GET.get('order_number', '')).strip().upper()
        email = (request.POST.get('email') or request.GET.get('email', '')).strip().lower()
        input_order_number = num
        input_email = email
        searched = True

        if num and email:
            try:
                order = Order.objects.get(order_number=num, email=email)
            except Order.DoesNotExist:
                error_msg = "No order found matching that Order Number and Email address. Please verify your confirmation email."
        elif num:
            # If user is logged in or provided order number directly
            try:
                order = Order.objects.get(order_number=num)
            except Order.DoesNotExist:
                error_msg = f"No order found with number '{num}'."
        else:
            error_msg = "Please provide both your Order Number and Email address."

    return render(request, 'orders/order_tracking.html', {
        'order': order,
        'searched': searched,
        'error_msg': error_msg,
        'input_order_number': input_order_number,
        'input_email': input_email,
        'meta_title': 'Real-Time Order Tracking & Logistics | Luckjary',
        'meta_description': 'Track the real-time status of your fine jewelry order, from our master atelier to your doorstep with insured white-glove courier service.',
    })


# --- Admin / Staff Centralized OMS Dashboard ---

def is_staff_check(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_staff_check, login_url='accounts:login')
def oms_dashboard(request):
    status_filter = request.GET.get('status')
    search_q = request.GET.get('q', '').strip()

    orders_qs = Order.objects.all().select_related('user').prefetch_related('items')

    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    if search_q:
        orders_qs = orders_qs.filter(
            Q(order_number__icontains=search_q) |
            Q(full_name__icontains=search_q) |
            Q(email__icontains=search_q) |
            Q(tracking_number__icontains=search_q)
        )

    # Metrics
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(payment_status='PAID').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    pending_count = Order.objects.filter(status='PENDING').count()
    processing_count = Order.objects.filter(status='PROCESSING').count()
    shipped_count = Order.objects.filter(status='SHIPPED').count()
    delivered_count = Order.objects.filter(status='DELIVERED').count()

    # Inventory alerts
    low_inventory_products = Product.objects.filter(inventory__lte=10).order_by('inventory')[:10]

    # Handle quick status update POST
    if request.method == 'POST' and 'update_order_status' in request.POST:
        ord_num = request.POST.get('order_number')
        new_status = request.POST.get('new_status')
        new_carrier = request.POST.get('carrier')
        new_tracking = request.POST.get('tracking_number')
        est_delivery = request.POST.get('estimated_delivery')
        log_note = request.POST.get('log_note')
        log_location = request.POST.get('log_location', 'Luckjary Fulfillment Center')

        ord_target = get_object_or_404(Order, order_number=ord_num)
        old_status = ord_target.status
        ord_target.status = new_status
        if new_carrier:
            ord_target.carrier = new_carrier
        if new_tracking:
            ord_target.tracking_number = new_tracking
        if est_delivery:
            try:
                ord_target.estimated_delivery = datetime.datetime.strptime(est_delivery, '%Y-%m-%d').date()
            except ValueError:
                pass
        ord_target.save()

        # Add timeline update
        title_map = {
            'PENDING': 'Order Verification',
            'PROCESSING': 'Handcrafting & Quality Control',
            'SHIPPED': 'Dispatched with Courier',
            'DELIVERED': 'Delivered to Recipient',
            'CANCELLED': 'Order Cancelled',
        }
        title = title_map.get(new_status, f"Status updated to {new_status}")
        desc = log_note or f"Order status updated from {old_status} to {new_status} by staff."

        OrderStatusUpdate.objects.create(
            order=ord_target,
            status=new_status,
            title=title,
            description=desc,
            location=log_location
        )
        messages.success(request, f"Order #{ord_target.order_number} updated to {new_status}.")
        return redirect('orders:oms_dashboard')

    return render(request, 'orders/oms/dashboard.html', {
        'orders': orders_qs[:30],
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_count': pending_count,
        'processing_count': processing_count,
        'shipped_count': shipped_count,
        'delivered_count': delivered_count,
        'low_inventory_products': low_inventory_products,
        'selected_status': status_filter,
        'search_q': search_q,
        'meta_title': 'Centralized OMS Admin Dashboard | Luckjary',
    })
