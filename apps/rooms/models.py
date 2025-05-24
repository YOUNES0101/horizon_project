from django.db import models
from django.core.validators import MinValueValidator
# Import JSONField if using older Django or database without native JSONField
# try:
#     from django.db.models import JSONField
# except ImportError:
#     from django.contrib.postgres.fields import JSONField # For PostgreSQL

ROOM_TYPE_CHOICES = [
    ('standard', 'Standard Room'),
    ('deluxe', 'Deluxe Room'),
    ('suite', 'Suite'),
    ('family', 'Family Room'),
    ('executive', 'Executive Room'),
]

AMENITIES_CHOICES = [
    ('wifi', 'WiFi'),
    ('tv', 'TV'),
    ('ac', 'Air Conditioning'),
    ('safe', 'Safe'),
    ('balcony', 'Balcony'),
    ('room_service', 'Room Service'),
    ('coffee', 'Coffee Maker'),
    ('bath', 'Bathtub'),
    ('view', 'Scenic View'),
]

class Room(models.Model):
    number = models.CharField(max_length=10, unique=True, verbose_name="Room Number")
    room_type = models.CharField(max_length=100, choices=ROOM_TYPE_CHOICES, verbose_name="Room Type")
    floor = models.PositiveIntegerField(verbose_name="Floor")
    amenities = models.JSONField(default=list, blank=True, verbose_name="Amenities")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price", default=100)
    is_available = models.BooleanField(default=True, verbose_name="Is Available")
    image = models.ImageField(upload_to='rooms/', null=True, blank=True, verbose_name="Image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
# Update __str__ to use get_room_type_display
        return f"Room {self.number} - {self.get_room_type_display()}"

    def get_price(self):
        return self.price


    class Meta:
        ordering = ['number']
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def get_image_url(self):
        if self.image:
            return self.image.url
        # Provide a path to a default image if no image is uploaded
        # Make sure you have a default image at static/images/default_room_image.jpg
        return '/static/images/default_room_image.jpg'

    def get_amenity_display(self):
        """Returns a list of full amenity names based on stored keys."""
        amenity_names = dict(AMENITIES_CHOICES)
        # Ensure we only return names for valid keys present in AMENITIES_CHOICES
        return [amenity_names.get(key) for key in self.amenities if key in amenity_names]

    def get_room_type_display(self):
        """Returns the full room type name based on the stored key."""
        room_type_names = dict(ROOM_TYPE_CHOICES)
        return room_type_names.get(self.room_type, self.room_type) # Return key itself if not found

