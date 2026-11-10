from decimal import Decimal
from catalog.models import Product

def cart_context(request):
    cart_session = request.session.get('cart', {})
    cart_items = []
    total_qty = 0
    subtotal = Decimal('0.00')

    product_ids = [int(pid) for pid in cart_session.keys() if pid.isdigit()]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

    for pid_str, item_info in cart_session.items():
        if not pid_str.isdigit():
            continue
        pid = int(pid_str)
        product = products.get(pid)
        if product:
            qty = item_info.get('quantity', 1)
            line_total = product.price * qty
            subtotal += line_total
            total_qty += qty
            cart_items.append({
                'product': product,
                'product_id': pid,
                'quantity': qty,
                'size': item_info.get('size', 'Standard'),
                'material': item_info.get('material', product.karat_metal),
                'line_total': line_total,
            })

    discount_amount = Decimal('0.00')
    coupon_code = request.session.get('coupon_code')
    if coupon_code and request.session.get('coupon_discount_percent'):
        pct = Decimal(request.session.get('coupon_discount_percent'))
        discount_amount = round((subtotal * pct) / Decimal('100.00'), 2)
    elif coupon_code and request.session.get('coupon_discount_amount'):
        discount_amount = Decimal(str(request.session.get('coupon_discount_amount')))
        if discount_amount > subtotal:
            discount_amount = subtotal

    final_total = max(Decimal('0.00'), subtotal - discount_amount)

    return {
        'cart_items': cart_items,
        'cart_count': total_qty,
        'cart_subtotal': subtotal,
        'cart_discount': discount_amount,
        'cart_total': final_total,
        'active_coupon': coupon_code,
    }
