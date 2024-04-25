from django.db import models
from django.db.models import F
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from core.choices import ModelActionChoicesBase
from core.utils import to_global_id


@deconstructible
class ImageFieldRename:
    def __init__(self, path: str, rename_attr: str):
        self.path = path.removesuffix("/")
        self.rename_attr = rename_attr

    def __call__(self, instance, filename):
        file_extension = filename.split(".")[-1]
        return f"{self.path}/{getattr(instance, self.rename_attr)}.{file_extension}"


class ModelWithMetadata(models.Model):
    is_active = models.BooleanField(_("is active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    metadata = models.JSONField(_("metadata"), default=dict, blank=True, null=True)

    class Meta:
        abstract = True

    def insert_metadata(self, data: dict):
        if not self.metadata:
            self.metadata = {}

        _keys = list(
            filter(
                lambda k: str(k).isnumeric(),
                self.metadata.keys(),
            )
        )
        _keys = list(
            map(
                lambda x: int(x),
                sorted(_keys),
            )
        )

        index = 1 if not _keys else _keys[-1] + 1
        self.metadata[index] = data

        return self.metadata

    @property
    def global_id(self):
        return to_global_id(self)


class SortableModel(models.Model):
    position = models.PositiveIntegerField(default=1, blank=True)
    divide_position_fields: list[str] = []

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_position = self.position

    def save(self, *args, **kwargs):
        reposition = kwargs.pop("reposition", True)

        Model = self._meta.model
        divide_filters = {}
        # divide positions based on fields
        if self.divide_position_fields is not None:
            for divide_field in self.divide_position_fields:
                divide_filters[divide_field] = getattr(self, divide_field)

        max_position_qs = Model.objects.all()
        if not self._state.adding:
            max_position_qs = max_position_qs.exclude(pk=self.pk)

        max_position = max_position_qs.filter(**divide_filters).aggregate(
            models.Max("position")
        )
        max_position = max_position["position__max"] or 0

        if self._state.adding or self.position != self._original_position:
            if self._state.adding:
                max_position = Model.objects.aggregate(models.Max("position"))[
                    "position__max"
                ]
                self.position = max_position + 1

            else:
                # If the position has changed, adjust other instances accordingly
                if self.position < self._original_position:
                    Model.objects.filter(
                        position__lt=self._original_position,
                        position__gte=self.position,
                        **divide_filters,
                    ).update(position=F("position") + 1)
                elif self.position > self._original_position:
                    Model.objects.filter(
                        position__gt=self._original_position,
                        position__lte=self.position,
                        **divide_filters,
                    ).update(position=F("position") - 1)

        if self.position > (max_position + 1):
            self.position = max_position + 1

        super().save(*args, **kwargs)

        if reposition:
            for idx, instance in enumerate(
                Model.objects.filter(**divide_filters).order_by("position").distinct()
            ):
                instance.position = idx + 1
                instance.save(reposition=False)


class ModelActionBase(ModelWithMetadata):
    action_choices = ModelActionChoicesBase
    changeable_fields = []

    by_system = models.BooleanField(_("by system"), default=False)
    user = models.ForeignKey(
        "user.User",
        verbose_name=_("user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    user_username = models.CharField(_("user username"), max_length=64)
    action = models.CharField(
        _("action"),
        max_length=128,
        db_index=True,
        choices=action_choices.choices,
        null=True,
        blank=True,
    )
    message = models.CharField(
        _("message"),
        max_length=256,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.user and not self.by_system:
            self.user_username = self.user.username
        if not self.user or self.by_system:
            self.user_username = "System"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[ {self.action} ]"

    class Meta:
        ordering = ["-created_at"]
        abstract = True
