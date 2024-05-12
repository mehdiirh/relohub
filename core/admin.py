import json

from django.contrib import admin
from django.contrib.admin import ModelAdmin, StackedInline
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


@admin.action(
    permissions=["change"],
    description=_("Active selected %(verbose_name_plural)s"),
)
def make_active(_model_admin, _request, queryset):
    queryset.update(is_active=True)


@admin.action(
    permissions=["change"],
    description=_("Deactivate selected %(verbose_name_plural)s"),
)
def make_inactive(_model_admin, _request, queryset):
    queryset.update(is_active=False)


class BaseModelAdmin(ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        readonly_fields = list(readonly_fields) + ["_metadata"]
        return readonly_fields

    def get_exclude(self, request, obj=None):
        exclude = super().get_exclude(request, obj) or []
        exclude = list(exclude) + ["metadata"]
        return exclude

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions["make_active"] = self.get_action(make_active)
        actions["make_inactive"] = self.get_action(make_inactive)
        return actions

    @staticmethod
    def _metadata(obj):
        return mark_safe(
            f'<pre style="background-color: #9a9a9a5c; padding: 12px;">'
            f"{json.dumps(obj.metadata)}</pre>"
        )


class SortableAdmin(ModelAdmin):
    def get_ordering(self, request):
        ordering = list(super().get_ordering(request))
        ordering.append("position")
        return tuple(ordering)

    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))
        if "id" not in list_display:
            list_display.insert(0, "id")

        list_display.append("position")
        return tuple(list_display)

    def get_list_editable(self, request):
        list_editable = list(self.list_editable)
        list_editable.append("position")
        return tuple(list_editable)

    def get_changelist_instance(self, request):
        self.list_editable = self.get_list_editable(request)
        return super().get_changelist_instance(request)


class BaseStackedInline(StackedInline):
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        readonly_fields = list(readonly_fields) + ["_metadata"]
        return readonly_fields

    def get_exclude(self, request, obj=None):
        exclude = super().get_exclude(request, obj) or []
        exclude = list(exclude) + ["metadata"]
        return exclude

    @staticmethod
    def _metadata(obj):
        return mark_safe(
            f'<pre style="background-color: #9a9a9a5c; padding: 12px;">'
            f"{json.dumps(obj.metadata)}</pre>"
        )


class SortableStackedInline(StackedInline):
    def get_ordering(self, request):
        ordering = list(super().get_ordering(request))
        ordering.append("position")
        return tuple(ordering)
