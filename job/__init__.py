from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class JobStatus(TextChoices):

    PARTIALLY_PROCEEDED = "PARTIALLY_PROCEEDED", _("Partially Proceeded")
    FULLY_PROCEEDED = "FULLY_PROCEEDED", _("Fully Proceeded")
    WAITING_FOR_REVIEW = "WAIT_FOR_REVIEW", _("Waiting For Review")
    APPROVED = "APPROVED", _("Approved")
    LISTED = "LISTED", _("Listed")
    REJECTED = "REJECTED", _("Rejected")
    EXPIRED = "EXPIRED", _("Expired")
