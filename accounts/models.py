from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils import timezone

class CustomUser(AbstractUser):
    # Using email as unique login identifier
    email = models.EmailField(unique=True, verbose_name="Email Address")
    phone_number = models.CharField(max_length=25, blank=True, null=True, verbose_name="Phone Number")
    
    # Email Verification
    is_email_verified = models.BooleanField(default=False, verbose_name="Email Verified")
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_token_created_at = models.DateTimeField(blank=True, null=True)
    
    # Newsletter & VIP Club
    newsletter_subscribed = models.BooleanField(default=True, verbose_name="Subscribed to Luckjary Privé Club")
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def generate_verification_token(self):
        self.email_verification_token = str(uuid.uuid4())
        self.verification_token_created_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'verification_token_created_at'])
        return self.email_verification_token

    def verify_email(self):
        self.is_email_verified = True
        self.email_verification_token = None
        self.save(update_fields=['is_email_verified', 'email_verification_token'])

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name} ({self.email})" if full_name else self.email


class Address(models.Model):
    ADDRESS_TYPES = [
        ('shipping', 'Shipping Address'),
        ('billing', 'Billing Address'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='shipping')
    full_name = models.CharField(max_length=150, verbose_name="Recipient Full Name")
    phone_number = models.CharField(max_length=30, verbose_name="Contact Phone")
    street_address = models.CharField(max_length=255, verbose_name="Street Address")
    apartment_suite = models.CharField(max_length=100, blank=True, null=True, verbose_name="Apt, Suite, Unit")
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, verbose_name="State / Province")
    postal_code = models.CharField(max_length=20, verbose_name="Postal / ZIP Code")
    country = models.CharField(max_length=100, default='United States')
    is_default = models.BooleanField(default=False, verbose_name="Default Address")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Addresses'
        ordering = ['-is_default', '-created_at']

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, address_type=self.address_type).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.street_address}, {self.city}, {self.country}"
