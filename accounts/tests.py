from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser, Address
from orders.models import Order

class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='lady_eleanor',
            email='eleanor@luckjary.com',
            password='Password123!',
            first_name='Eleanor',
            last_name='Vance',
            is_email_verified=True
        )

    def test_registration_generates_verification_token(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Sophia',
            'last_name': 'Loren',
            'email': 'sophia.loren@luxury.com',
            'password': 'LuxurySecret2026!',
            'password_confirm': 'LuxurySecret2026!',
            'newsletter': 'on'
        })
        self.assertEqual(response.status_code, 302)
        
        new_user = CustomUser.objects.get(email='sophia.loren@luxury.com')
        self.assertFalse(new_user.is_email_verified)
        self.assertIsNotNone(new_user.email_verification_token)

        # Test verification link
        verify_url = reverse('accounts:verify_email', kwargs={'token': new_user.email_verification_token})
        verify_resp = self.client.get(verify_url)
        self.assertEqual(verify_resp.status_code, 200)

        new_user.refresh_from_db()
        self.assertTrue(new_user.is_email_verified)
        self.assertIsNone(new_user.email_verification_token)

    def test_user_login_and_profile_access(self):
        login_resp = self.client.post(reverse('accounts:login'), {
            'email': 'eleanor@luckjary.com',
            'password': 'Password123!'
        })
        self.assertEqual(login_resp.status_code, 302)

        profile_resp = self.client.get(reverse('accounts:profile'))
        self.assertEqual(profile_resp.status_code, 200)
        self.assertContains(profile_resp, 'Eleanor Vance')

    def test_saved_address_management(self):
        self.client.force_login(self.user)
        # Add Address
        resp = self.client.post(reverse('accounts:addresses'), {
            'action': 'add',
            'full_name': 'Eleanor Vance',
            'phone_number': '+1 212 555 0199',
            'street_address': '740 Park Ave',
            'apartment_suite': '18B',
            'city': 'New York',
            'state_province': 'NY',
            'postal_code': '10021',
            'country': 'United States',
            'is_default': 'on'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Address.objects.filter(user=self.user).count(), 1)
        addr = Address.objects.filter(user=self.user).first()
        self.assertTrue(addr.is_default)

    def test_guest_post_purchase_account_creation(self):
        # Create a guest order
        order = Order.objects.create(
            order_number='LCK-202611-GUEST01',
            email='guest.shopper@example.com',
            full_name='Charlotte Dupré',
            phone='+1 415 882 9901',
            shipping_street='1000 California St',
            shipping_city='San Francisco',
            shipping_state='CA',
            shipping_zip='94108',
            subtotal=1650.00,
            total_amount=1650.00
        )
        self.assertIsNone(order.user)

        # Convert to full account
        convert_url = reverse('accounts:guest_convert', kwargs={'order_number': order.order_number})
        resp = self.client.post(convert_url, {
            'password': 'GuestPassword2026!',
            'password_confirm': 'GuestPassword2026!'
        })
        self.assertEqual(resp.status_code, 302)

        created_user = CustomUser.objects.get(email='guest.shopper@example.com')
        self.assertTrue(created_user.is_email_verified)
        order.refresh_from_db()
        self.assertEqual(order.user, created_user)
