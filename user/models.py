import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from core.models import ModelWithMetadata
from core.utils import get_random_hex


class User(ModelWithMetadata, AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    is_active = models.BooleanField(default=True)
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    token = models.CharField(
        _("token"),
        help_text=_("Api token. Clear to change."),
        max_length=32,
        unique=True,
        blank=True,
    )
    email = models.EmailField(_("email address"), blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )

    phone = PhoneNumberField(verbose_name=_("phone"), null=True, blank=True)
    currency = models.CharField(_("Currency"), default="IRT", max_length=6)

    invited_by = models.ForeignKey(
        verbose_name=_("invited by"),
        to="self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    joined_by_campaign = models.ForeignKey(
        verbose_name=_("joined by campaign"),
        related_name="users",
        to="AdvertiseCampaign",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def save(self, *args, **kwargs):
        if not self.token:
            while True:
                token = get_random_hex()
                if User.objects.filter(token__exact=token).exists():
                    continue
                self.token = token
                break

        super().save(*args, **kwargs)


class AdvertiseCampaignQuerySet(models.QuerySet):

    def active(self):
        now = timezone.now()
        return self.filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now),
            start_date__lte=now,
            is_active=True,
        )

    def get_by_code(self, code: str):
        return self.get(code__exact=code)


class AdvertiseCampaign(ModelWithMetadata):
    name = models.CharField(verbose_name=_("name"), max_length=256)
    code = models.CharField(
        verbose_name=_("code"),
        help_text=_("leave blank to auto generate"),
        max_length=16,
        blank=True,
    )
    start_date = models.DateTimeField(verbose_name=_("start date"))
    end_date = models.DateTimeField(verbose_name=_("end date"), null=True, blank=True)

    objects = AdvertiseCampaignQuerySet.as_manager()

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                _code = str(uuid.uuid4()).split("-")[0]
                if not AdvertiseCampaign.objects.filter(code__exact=_code):
                    self.code = _code
                    break

        super().save()

    def __str__(self):
        return f"{self.name} [{self.code}]"

    def active(self) -> bool:
        now = timezone.now()
        return (
            self.is_active
            and self.start_date <= now
            and (self.end_date is None or self.end_date >= now)
        )

    @property
    def user_count(self) -> int:
        return self.users.count()
