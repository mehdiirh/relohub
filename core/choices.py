from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class ModelActionChoicesBase(TextChoices):
    UNDEFINED = "UNDEFINED", _("Undefined")
