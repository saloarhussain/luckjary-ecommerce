"""
Shared real-time database telemetry helpers for the Luckjary Admin & OMS Console.
"""

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.db.models import Count, Q, Sum
from django.utils.timesince import timesince

USD_TO_INR = 83.1527


def format_indian_number(value):
    """Formats an integer using Indian comma grouping (e.g. 928399 -> '9,28,399')."""
    try:
        num = int(round(float(value or 0)))
    except (TypeError, ValueError):
        return "0"
    sign = "-" if num < 0 else ""
    s = str(abs(num))
    if len(s) <= 3:
        return f"{sign}{s}"
    last3 = s[-3:]
    rest = s[:-3]
    groups = []
    while len(rest) > 2:
        groups.append(rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.append(rest)
    return f"{sign}{','.join(reversed(groups))},{last3}"


def serialize_order_summary(order):
    """Serializes an Order model instance into a unified dict for templates and live polling."""
    items = list(order.items.all())
    first_item = items[0] if items else None
    primary_item_title = first_item.product_name if first_item else "Bespoke Order"
    item_count = sum((it.quantity or 1) for it in items) if items else 0
    total_usd_num = float(order.total_amount or 0)
    total_inr_num = int(round(total_usd_num * USD_TO_INR))

    name_parts = [p for p in (order.full_name or "").strip().split() if p]
    if len(name_parts) >= 2:
        initials = (name_parts[0][0] + name_parts[-1][0]).upper()
    elif len(name_parts) == 1:
        initials = name_parts[0][:2].upper()
    else:
        initials = "CL"

    status_meta = {
        'PENDING': ('unfulfilled', 'Unfulfilled'),
        'PROCESSING': ('qc', 'In Atelier QC'),
        'SHIPPED': ('transit', 'In Transit'),
        'DELIVERED': ('delivered', 'Delivered'),
        'CANCELLED': ('cancelled', 'Cancelled'),
    }
    filter_key, status_label = status_meta.get(order.status, ('unfulfilled', order.get_status_display()))

    payment_labels = {
        'PAID': 'Paid',
        'PENDING': 'Pending',
        'REFUNDED': 'Refunded',
    }
    payment_label = payment_labels.get(order.payment_status, order.get_payment_status_display())

    created_local = order.created_at
    date_display = created_local.strftime('%b %d, %Y') if created_local else ''
    time_display = created_local.strftime('%H:%M') if created_local else ''

    return {
        'id': order.id,
        'order_number': order.order_number,
        'date_display': date_display,
        'time_display': time_display,
        'full_name': order.full_name,
        'email': order.email,
        'phone': order.phone or '',
        'initials': initials,
        'payment_status': order.payment_status,
        'payment_label': payment_label,
        'status': order.status,
        'filter_key': filter_key,
        'status_label': status_label,
        'carrier': order.carrier or '',
        'tracking_number': order.tracking_number or '',
        'total_usd_num': total_usd_num,
        'total_usd': f"{total_usd_num:,.2f}",
        'total_inr_num': total_inr_num,
        'total_inr': format_indian_number(total_inr_num),
        'primary_item_title': primary_item_title,
        'item_count': item_count,
        'edit_url': f"/admin/orders/order/{order.id}/change/",
        'search_blob': f"{order.full_name} {order.email} {order.order_number} {primary_item_title} {order.tracking_number or ''}".lower(),
    }


def get_order_counts():
    """Returns real-time order counts grouped by fulfillment status."""
    from orders.models import Order

    agg = Order.objects.aggregate(
        all_count=Count('id'),
        unfulfilled=Count('id', filter=Q(status='PENDING')),
        qc=Count('id', filter=Q(status='PROCESSING')),
        transit=Count('id', filter=Q(status='SHIPPED')),
        delivered=Count('id', filter=Q(status='DELIVERED')),
        cancelled=Count('id', filter=Q(status='CANCELLED')),
    )
    return {
        'all': agg['all_count'] or 0,
        'unfulfilled': agg['unfulfilled'] or 0,
        'qc': agg['qc'] or 0,
        'transit': agg['transit'] or 0,
        'delivered': agg['delivered'] or 0,
        'cancelled': agg['cancelled'] or 0,
    }


def get_atelier_live_telemetry(summary_only=False):
    """Queries live database metrics, recent orders, and recent admin activity."""
    from accounts.models import CustomUser
    from catalog.models import Product
    from orders.models import Coupon, Order

    valid_paid_q = Q(payment_status='PAID') & ~Q(status='CANCELLED')
    order_stats = Order.objects.aggregate(
        rev=Sum('total_amount', filter=valid_paid_q),
        paid_orders=Count('id', filter=valid_paid_q),
        total_orders=Count('id'),
        pending=Count('id', filter=Q(status='PENDING')),
        processing=Count('id', filter=Q(status='PROCESSING')),
        shipped=Count('id', filter=Q(status='SHIPPED')),
        delivered=Count('id', filter=Q(status='DELIVERED')),
    )
    total_products = Product.objects.count()
    total_orders = order_stats['total_orders'] or 0

    if summary_only:
        return {
            'total_products': total_products,
            'total_orders': total_orders,
        }

    total_customers = CustomUser.objects.count()
    active_coupons = Coupon.objects.filter(active=True).count()

    rev = float(order_stats['rev'] or 0)
    paid_orders = order_stats['paid_orders'] or 0
    pending = order_stats['pending'] or 0
    processing = order_stats['processing'] or 0
    shipped = order_stats['shipped'] or 0
    delivered = order_stats['delivered'] or 0

    avg_aov = (rev / paid_orders) if paid_orders > 0 else 0.0
    rev_inr = int(round(rev * USD_TO_INR))
    avg_aov_inr = int(round(avg_aov * USD_TO_INR))

    recent_order_objs = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')[:6]
    recent_orders = [serialize_order_summary(o) for o in recent_order_objs]

    action_verbs = {
        ADDITION: 'added',
        CHANGE: 'modified',
        DELETION: 'removed',
    }
    log_entries = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')[:5]
    recent_activity = []
    for entry in log_entries:
        actor = (entry.user.first_name or entry.user.username) if entry.user else 'System'
        verb = action_verbs.get(entry.action_flag, 'updated')
        model_label = entry.content_type.name if entry.content_type else 'item'
        recent_activity.append({
            'actor': actor,
            'verb': verb,
            'action_flag': entry.action_flag,
            'model_label': model_label,
            'object_repr': entry.object_repr,
            'time_ago': f"{timesince(entry.action_time)} ago" if entry.action_time else 'Just now',
        })

    return {
        'total_revenue': f"{rev:,.2f}",
        'total_revenue_inr': format_indian_number(rev_inr),
        'total_orders': total_orders,
        'pending_count': pending,
        'processing_count': processing,
        'unfulfilled_count': pending + processing,
        'shipped_count': shipped,
        'delivered_count': delivered,
        'avg_aov': f"{avg_aov:,.2f}",
        'avg_aov_inr': format_indian_number(avg_aov_inr),
        'total_products': total_products,
        'total_customers': total_customers,
        'active_coupons': active_coupons,
        'recent_orders': recent_orders,
        'recent_activity': recent_activity,
    }
