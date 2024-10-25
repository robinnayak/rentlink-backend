from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from rooms.locations import LOCATION_CHOICES
from django.core.mail import send_mail
from django.conf import settings
from cloudinary.models import CloudinaryField
# Custom user manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50,blank=True)
    password = models.CharField(
        max_length=128,
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$',
                message=_('Password must be at least 8 characters long and include both letters and numbers.')
            )
        ]
    )
    contact_number = models.CharField(
    max_length=15,
    help_text="Contact phone number"
    )
    is_landowner = models.BooleanField(default=False, help_text="Check this if the user is a landowner, otherwise they will be a leasee.")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically assign the user to the appropriate group
        from django.contrib.auth.models import Group
        if self.is_landowner:
            group, created = Group.objects.get_or_create(name='Landlord')
            Landlord.objects.get_or_create(user=self)
        else:
            group, created = Group.objects.get_or_create(name='Leasee')
            Leasee.objects.get_or_create(user=self)
        self.groups.add(group)

# Landlord Model
class Landlord(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='landlord_profile')
    address = models.CharField(max_length=255, choices=LOCATION_CHOICES, help_text="Select a location")
    sub_address = models.CharField(max_length=255, null=True, blank=True, help_text="Street name or additional address details")
    date_of_registration = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - Landlord"

# Leasee (Lessee) Model
class Leasee(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='leasee_profile')
    address = models.CharField(max_length=255, choices=LOCATION_CHOICES, help_text="Select a location")
    sub_address = models.CharField(max_length=255, null=True, blank=True, help_text="Street name or additional address details")
    preferred_location = models.CharField(max_length=255, null=True, blank=True, help_text="Preferred location for lease")
    reviews = models.TextField(null=True, blank=True, help_text="Reviews from previous landlords")
    location_url = models.URLField(max_length=500, null=True, blank=True, help_text="URL for the map location of the renter")

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - Leasee"

# Rent Giver is referenced through the Landlord model (assumed it's linked to CustomUser)
class Room(models.Model):
    rent_giver = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name='rooms')
    title = models.CharField(max_length=255, help_text="A brief title for the room.")
    description = models.TextField(help_text="Detailed description of the room and its facilities.")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rental price (can be per day, week, or month).")
    
    # Location Fields
    address = models.CharField(max_length=255, help_text="Full address of the room.")
    sub_address = models.CharField(max_length=255, help_text="Street name or specific sub-address.")
    location_url = models.URLField(max_length=500, help_text="URL for the map location of the room.")
    
    # Amenities
    has_electricity = models.BooleanField(default=False, help_text="Is 24-hour electricity available?")
    has_wifi = models.BooleanField(default=False, help_text="Is Wi-Fi service available?")
    has_water_supply = models.BooleanField(default=False, help_text="Is 24/7 water supply available?")
    has_parking = models.BooleanField(default=False, help_text="Is parking available?")
    
    # Availability and Photos
    is_available = models.BooleanField(default=True, help_text="Is the room available for rent?")
    # photos = models.ImageField(upload_to='room_photos/', null=True, blank=True, help_text="Upload room photos.")
    photos = CloudinaryField('room_photos/', null=True, blank=True, help_text="Upload room photos.")
    
    # Ratings and Reviews
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="Overall rating from reviews.")
    
    # Rules and Policies
    pets_allowed = models.BooleanField(default=False, help_text="Are pets allowed?")
    smoking_allowed = models.BooleanField(default=False, help_text="Is smoking allowed?")
    curfew_time = models.TimeField(null=True, blank=True, help_text="Is there any curfew?")
    
    def __str__(self):
        return f"{self.title} - {self.rent_giver.user.email}"
    
    def has_deposit(self, leasee=None, landlord=None):
        """Check if the room has a deposit."""
        if leasee:
            return self.room_deposits.filter(leasee=leasee).exists()
        elif landlord:
            return self.room_deposits.filter(landlord=landlord).exists()
        return False

class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_images')
    image = CloudinaryField('room_image', null=True,blank=True, help_text="Upload an image of the room.")

    def __str__(self):
        return f"Image for {self.room.title} - {self.room.rent_giver.user.email}"

class Deposit(models.Model):
    leasee = models.ForeignKey(Leasee, on_delete=models.CASCADE, blank=True,null=True ,related_name='leasee_deposits')
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE,blank=True,null=True, related_name='landlord_deposits')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount of the deposit required.")
    payment_status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending', help_text="Status of the deposit payment.")
    deposit_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Deposit for {self.room.title} by {self.leasee.user.email} - {self.payment_status}"

    def is_paid(self):
        """Check if the deposit is fully paid."""
        return self.payment_status == 'paid'

class VisitRequest(models.Model):
    leasee = models.ForeignKey(Leasee, on_delete=models.CASCADE, related_name='visit_requests')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='visit_requests')
    request_date = models.DateTimeField(auto_now_add=True, help_text="Date and time when the visit request was made.")
    
    VISIT_STATUS_CHOICES = [
        ('pending', 'Pending'),     # Request is waiting for approval
        ('confirmed', 'Confirmed'), # Visit confirmed by the landlord
        ('cancelled', 'Cancelled'), # Visit cancelled
    ]
    status = models.CharField(max_length=10, choices=VISIT_STATUS_CHOICES, default='pending', help_text="Status of the visit request.")
    
    def __str__(self):
        return f"Visit request for {self.room.title} by {self.leasee.user.email} - {self.status}"
    
    def confirm(self):
        """Confirm the visit request."""
        self.status = 'confirmed'
        self.save()
    
    def cancel(self):
        """Cancel the visit request."""
        self.status = 'cancelled'
        self.save()
    
    def notify_landlord_by_email(self):
        """Notify the landlord via email when a visit request is made."""
        subject = "New Visit Request"
        message = f"Dear {self.room.rent_giver.user.first_name},\n\n{self.leasee.user.first_name} {self.leasee.user.last_name} has requested to visit your room titled '{self.room.title}'.\n\nPlease review and confirm or cancel the request."
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [self.room.rent_giver.user.email]
        
        send_mail(subject, message, from_email, recipient_list)

    def notify_landlord(self):
        """Create an in-app notification for the landlord."""
        message = f"{self.leasee.user.first_name} {self.leasee.user.last_name} has requested to visit your room titled '{self.room.title}'."
        Notification.objects.create(user=self.room.rent_giver.user, message=message)
    
    
    def save(self, *args, **kwargs):
        # Only send notification when a new request is created
        if not self.pk:
            super().save(*args, **kwargs)
            self.notify_landlord_by_email()
            self.notify_landlord()
        else:
            super().save(*args, **kwargs)

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField(help_text="Notification message")
    is_read = models.BooleanField(default=False, help_text="Has the notification been read?")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email} - {'Read' if self.is_read else 'Unread'}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

class ContactForm(models.Model):
    # Subject choices
    SUBJECT_CHOICES = [
        ('problem', 'Problem'),
        ('feedback', 'Feedback'),
        ('suggestion', 'Suggestion'),
        ('question', 'Question'),
    ]

    # Status choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
    ]

    # Model fields
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # To track when the form was submitted

    def __str__(self):
        return f'{self.name} - {self.subject} ({self.status})'
