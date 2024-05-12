import pytz
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import ModelWithMetadata, ImageFieldRename
from job import JobStatus


class Company(ModelWithMetadata):
    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")

    name = models.CharField(_("name"), max_length=256)
    universal_name = models.CharField(_("universal name"), max_length=256)
    linkedin_id = models.CharField(
        _("linkedin ID"),
        max_length=32,
        unique=True,
        db_index=True,
    )
    logo = models.ImageField(_("logo"), upload_to="company/", null=True, blank=True)

    def __str__(self):
        return f"{self.name} #{self.linkedin_id}"


class JobTitle(ModelWithMetadata):
    class Meta:
        verbose_name = _("Job Title")
        verbose_name_plural = _("Job Titles")

    title = models.CharField(_("title"), max_length=128)
    parent = models.ForeignKey(
        to="self",
        verbose_name=_("parent"),
        related_name="children",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    other_names = models.TextField(
        _("other names"),
        max_length=512,
        null=True,
        blank=True,
        help_text=_("semicolon separated names"),
    )
    linkedin_id = models.CharField(
        _("linkedin ID"),
        max_length=32,
        unique=True,
        db_index=True,
    )

    def get_other_names(self):
        return self.other_names.split(";") if self.other_names else []

    def add_other_name(self, name: str):
        other_names = self.get_other_names()
        if name.lower() not in list(map(lambda n: n.lower(), other_names)):
            other_names.append(name)
        self.other_names = ";".join(other_names)
        self.save()

    def get_children(self, recursive=False):

        children = self.children.all()
        if recursive:
            for child in children:
                children = children.union(child.get_children(recursive=True))

        return children

    def save(self, *args, **kwargs):
        if self.other_names:
            names = []
            for n in self.other_names.split(";"):
                if n and n not in names:
                    names.append(n.strip())
            self.other_names = ";".join(names)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} #{self.linkedin_id}"


class JobSkill(ModelWithMetadata):
    class Meta:
        verbose_name = _("Job Skill")
        verbose_name_plural = _("Job Skills")

    name = models.CharField(_("name"), max_length=128)
    linkedin_id = models.CharField(
        _("linkedin ID"),
        max_length=32,
        unique=True,
        db_index=True,
    )

    def __str__(self):
        return f"{self.name} #{self.linkedin_id}"


class JobLocation(ModelWithMetadata):
    class Meta:
        verbose_name = _("Job Location")
        verbose_name_plural = _("Job Locations")

    title = models.CharField(_("title"), max_length=128)
    iso_code = models.CharField(_("ISO code"), max_length=4)
    linkedin_geo_id = models.CharField(_("linkedin geo ID"), max_length=32)
    flag_emoji = models.CharField(_("flag emoji"), max_length=8)
    flag_image = models.ImageField(
        _("flag image"),
        upload_to=ImageFieldRename("job/locations/flags", "iso_code"),
    )

    def __str__(self):
        return f"{self.flag_emoji} {self.title} #{self.linkedin_geo_id}"


class Job(ModelWithMetadata):
    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")

    linkedin_id = models.CharField(
        _("linkedin ID"),
        max_length=32,
        unique=True,
        db_index=True,
    )

    title = models.CharField(_("title"), max_length=256)
    description = models.TextField(
        _("description"),
        null=True,
        blank=True,
    )
    attributes = models.JSONField(
        _("attributes"),
        default=dict,
        blank=True,
    )
    full_location = models.CharField(
        _("full location"),
        max_length=128,
        null=True,
        blank=True,
    )
    listed_at = models.DateTimeField(_("listed at"), null=True, blank=True)

    on_site = models.BooleanField(_("on-site"), default=False)
    hybrid = models.BooleanField(_("hybrid"), default=False)
    remote = models.BooleanField(_("remote"), default=False)

    full_time = models.BooleanField(_("full_time"), default=False)
    part_time = models.BooleanField(_("part_time"), default=False)
    contract = models.BooleanField(_("contract"), default=False)

    status = models.CharField(
        _("status"),
        max_length=32,
        choices=JobStatus.choices,
        default=JobStatus.PARTIALLY_PROCEEDED,
    )

    company = models.ForeignKey(
        to=Company,
        verbose_name=_("company"),
        related_name="jobs",
        on_delete=models.CASCADE,
        limit_choices_to={"is_active": True},
        null=True,
        blank=True,
    )
    location = models.ForeignKey(
        to=JobLocation,
        verbose_name=_("location"),
        related_name="jobs",
        on_delete=models.CASCADE,
        limit_choices_to={"is_active": True},
    )

    job_titles = models.ManyToManyField(
        to=JobTitle,
        verbose_name=_("job titles"),
        related_name="jobs",
        limit_choices_to={"is_active": True, "parent__isnull": True},
        blank=True,
    )
    job_skills = models.ManyToManyField(
        to=JobSkill,
        verbose_name=_("job skills"),
        related_name="jobs",
        limit_choices_to={"is_active": True},
        blank=True,
    )

    points = models.PositiveIntegerField(_("points"), default=0)

    def __str__(self):
        return f"{self.title} @ {self.company or '-'}"

    def save(self, *args, **kwargs):
        if isinstance(self.listed_at, (int, float)):
            try:
                self.listed_at = timezone.datetime.fromtimestamp(
                    self.listed_at, tz=pytz.UTC
                )
            except ValueError:
                self.listed_at = timezone.datetime.fromtimestamp(
                    self.listed_at / 1000, tz=pytz.UTC
                )

        super().save(*args, **kwargs)
