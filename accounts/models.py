from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """TIMBANG user: one account, exactly one role (BR-01).

    Built on Django's AbstractUser so password hashing, sessions, login and
    permissions all use Django's built-in authentication. `is_active` is the
    account status (BR-07): a deactivated user cannot log in.
    """

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        STAFF = "STAFF", "Staff"

    # The SDD stores a single full_name, so the split name fields are removed.
    first_name = None
    last_name = None

    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=120, unique=True)  # BR-02
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STAFF)
    contact_number = models.CharField(
        max_length=20, blank=True
    )
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ["email", "full_name"]

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split(" ")[0] if self.full_name else self.username

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_shop_staff(self):
        return self.role == self.Role.STAFF

    @property
    def initial(self):
        return (self.full_name or self.username)[:1].upper()

    @property
    def dashboard_url_name(self):
        return "accounts:owner_dashboard" if self.is_owner else "accounts:staff_dashboard"
