from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, Address
from orders.models import Order
import uuid

def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        newsletter = request.POST.get('newsletter') == 'on'

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, 'accounts/register.html')

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register.html')

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, 'accounts/register.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists. Please log in.")
            return redirect('accounts:login')

        username = email.split('@')[0]
        # ensure unique username
        base_username = username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            newsletter_subscribed=newsletter,
            is_email_verified=False
        )

        token = user.generate_verification_token()
        verification_link = request.build_absolute_uri(
            reverse('accounts:verify_email', kwargs={'token': token})
        )

        # Send simulated/console verification email
        try:
            send_mail(
                subject="Verify Your Luckjary Atelier Account",
                message=f"Welcome to Luckjary. Please verify your email by clicking: {verification_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass

        request.session['verification_pending_email'] = email
        request.session['demo_verification_link'] = verification_link

        return redirect('accounts:verify_email_sent')

    return render(request, 'accounts/register.html', {
        'meta_title': 'Join Luckjary Privé | Create an Account',
        'meta_description': 'Create your Luckjary account to track fine jewelry orders, enjoy bespoke concierge service, and save your wishlists.',
    })


def verify_email_sent(request):
    email = request.session.get('verification_pending_email', 'your email address')
    demo_link = request.session.get('demo_verification_link')
    return render(request, 'accounts/verify_email_sent.html', {
        'email': email,
        'demo_link': demo_link,
        'meta_title': 'Verification Email Sent | Luckjary',
    })


def verify_email(request, token):
    try:
        user = CustomUser.objects.get(email_verification_token=token)
        user.verify_email()
        login(request, user)
        messages.success(request, f"Welcome to Luckjary Privé, {user.first_name or user.email}! Your email has been verified successfully.")
        return render(request, 'accounts/verify_email_status.html', {
            'success': True,
            'user': user,
            'meta_title': 'Account Verified | Luckjary',
        })
    except CustomUser.DoesNotExist:
        messages.error(request, "Invalid or expired email verification link.")
        return render(request, 'accounts/verify_email_status.html', {
            'success': False,
            'meta_title': 'Verification Failed | Luckjary',
        })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    next_url = request.GET.get('next', 'accounts:profile')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # Authenticate by email
        user = authenticate(request, email=email, password=password)
        if user is None:
            # Fallback if username was passed
            try:
                u_obj = CustomUser.objects.get(email=email)
                user = authenticate(request, username=u_obj.username, password=password)
            except CustomUser.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or 'esteemed guest'}.")
            return redirect(next_url if next_url else 'accounts:profile')
        else:
            messages.error(request, "Invalid email address or password.")

    return render(request, 'accounts/login.html', {
        'next': next_url,
        'meta_title': 'Client Sign In | Luckjary Fine Jewelry',
        'meta_description': 'Sign in to access your Luckjary order history, bespoke jewelry requests, and saved addresses.',
    })


def logout_view(request):
    logout(request)
    messages.info(request, "You have been securely signed out. We look forward to welcoming you back soon.")
    return redirect('core:home')


@login_required
def profile_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    addresses = Address.objects.filter(user=request.user)
    
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'orders': orders,
        'addresses': addresses,
        'meta_title': 'My Account & Vault | Luckjary',
    })


@login_required
def addresses_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            full_name = request.POST.get('full_name')
            phone = request.POST.get('phone_number')
            street = request.POST.get('street_address')
            apt = request.POST.get('apartment_suite', '')
            city = request.POST.get('city')
            state = request.POST.get('state_province')
            zip_code = request.POST.get('postal_code')
            country = request.POST.get('country', 'United States')
            addr_type = request.POST.get('address_type', 'shipping')
            is_default = request.POST.get('is_default') == 'on'

            Address.objects.create(
                user=request.user,
                address_type=addr_type,
                full_name=full_name,
                phone_number=phone,
                street_address=street,
                apartment_suite=apt,
                city=city,
                state_province=state,
                postal_code=zip_code,
                country=country,
                is_default=is_default
            )
            messages.success(request, "Address saved to your address book.")
            return redirect('accounts:addresses')

        elif action == 'delete':
            addr_id = request.POST.get('address_id')
            addr = get_object_or_404(Address, id=addr_id, user=request.user)
            addr.delete()
            messages.success(request, "Address removed.")
            return redirect('accounts:addresses')

    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/addresses.html', {
        'addresses': addresses,
        'meta_title': 'Saved Addresses | Luckjary Client Vault',
    })


def guest_create_account(request, order_number):
    """
    Automatic post-purchase account creation prompt for Guest Checkout users.
    """
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == 'POST':
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if not password or len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return redirect('orders:order_success', order_number=order.order_number)

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('orders:order_success', order_number=order.order_number)

        email = order.email
        if CustomUser.objects.filter(email=email).exists():
            # Link order to existing user
            existing_user = CustomUser.objects.get(email=email)
            order.user = existing_user
            order.save()
            messages.info(request, "An account with your email already exists. Your order has been linked. Please log in.")
            return redirect('accounts:login')

        # Create new user
        names = order.full_name.split(' ', 1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else ''
        username = email.split('@')[0]

        counter = 1
        base_username = username
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        new_user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=order.phone,
            is_email_verified=True # Verified by checkout transaction
        )

        # Link this order and any other orders with matching email
        Order.objects.filter(email=email).update(user=new_user)

        # Save shipping address to user's address book
        Address.objects.create(
            user=new_user,
            address_type='shipping',
            full_name=order.full_name,
            phone_number=order.phone or '',
            street_address=order.shipping_street,
            apartment_suite=order.shipping_apartment or '',
            city=order.shipping_city,
            state_province=order.shipping_state,
            postal_code=order.shipping_zip,
            country=order.shipping_country,
            is_default=True
        )

        login(request, new_user)
        messages.success(request, f"Congratulations {first_name}! Your Luckjary account has been created. You can now track your order anytime.")
        return redirect('accounts:profile')

    return redirect('orders:order_success', order_number=order.order_number)
