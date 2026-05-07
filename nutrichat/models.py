import base64
import logging

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from markdownx.models import MarkdownxField

log = logging.getLogger(__name__)


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
        # Superusers have no role
        extra_fields.setdefault("is_admin", True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser):
    class Role(models.TextChoices):
        NUTRITIONIST = "NUTRITIONIST", "Nutritionist"
        CUSTOMER = "CUSTOMER", "Customer"

    username = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    name = models.CharField(max_length=150, blank=True)
    surname = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role, blank=True)
    nutritionist = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="customers",
        limit_choices_to={"role": Role.NUTRITIONIST},
    )
    description = MarkdownxField(blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class Conversation(models.Model):
    """Conversation between user and LLM. The checkpoints of the conversation are stored in the tables managed by
    Langraph via AsyncPostgresSaver. The id of the conversation is used to match the thread_id in the graph config, but
    deleting a Conversation does not cascade to LangGraph checkpoint data; cleanup must be handled manually."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    title = models.CharField(
        max_length=255, blank=True
    )  # Auto-generated from first message
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_updated"]

    def __str__(self):
        return self.title or f"Conversation {self.pk}"


class Attachment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="attachments/%Y-%m/")
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def read_as_base64(self) -> str | None:
        try:
            with self.file.open("rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            log.exception(
                f"Failed to read attachment {self.file} (id={self.id}) for user={self.user.username}"
            )
            return None
