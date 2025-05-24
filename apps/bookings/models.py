from django.db import models
from django.conf import settings
from apps.rooms.models import Room
import uuid

class Booking(models.Model):
    # Relationships
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')

    # Booking details
    booking_number = models.CharField(max_length=20, unique=True, editable=False)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    num_guests = models.PositiveIntegerField()

    # Guest information
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=20)

    # Status and payment
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Special requests
    special_requests = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'



    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash'),
    ]
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='credit_card',
    )

    def __str__(self):
        return f"Booking {self.booking_number} - {self.guest_name}"

    def save(self, *args, **kwargs):
        # Generate a unique booking number if not already set
        if not self.booking_number:
            self.booking_number = self.generate_booking_number()
        super().save(*args, **kwargs)

    def generate_booking_number(self):
        """Generate a unique booking number."""
        # Format: HZ-YYYYMMDD-XXXX where XXXX is a random string
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        random_str = uuid.uuid4().hex[:4].upper()
        return f"HZ-{date_str}-{random_str}"

    @property
    def duration(self):
        """Calculate the duration of stay in days."""
        return (self.check_out_date - self.check_in_date).days

    @property
    def is_active(self):
        """Check if the booking is active (confirmed or pending)."""
        return self.status in ['confirmed', 'pending']

    @property
    def is_past(self):
        """Check if the booking is in the past."""
        from django.utils import timezone
        return self.check_out_date < timezone.now().date()

    def calculate_total_price(self):
        """Calculate the total price based on room rate and duration."""
        # Use room's price field directly
        from decimal import Decimal
        daily_rate = self.room.price
        return daily_rate * self.duration

