from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Users must have an email address")

        user = self.model(
            username=self.normalize_email(username).lower(),
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """Superusers have no type"""
        extra_fields.setdefault("is_admin", True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser):
    class UserType(models.TextChoices):
        NUTRITIONIST = "NUTRITIONIST", "Nutritionist"
        CUSTOMER = "CUSTOMER", "Customer"

    username = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        return True

    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        return True

    @property
    def is_staff(self):
        """Is the user a member of staff?"""
        return self.is_admin

    @property
    def type(self):
        """Derives user type from profile existence"""
        if hasattr(self, 'nutritionist'):
            return self.UserType.NUTRITIONIST
        elif hasattr(self, 'customer'):
            return self.UserType.CUSTOMER
        return None

    @property
    def profile(self):
        """Returns the user's profile based on their type"""
        return getattr(self, 'nutritionist', None) or getattr(self, 'customer', None)


class Nutritionist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='nutritionist',
    )

    def __str__(self):
        return f"{self.user.username}"


class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer',
    )
    nutritionist = models.ForeignKey(
        Nutritionist,
        on_delete=models.CASCADE,
        related_name='customers'
    )

    def __str__(self):
        return f"{self.user.username}"
