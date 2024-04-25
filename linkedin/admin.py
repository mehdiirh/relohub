from django.contrib import admin

from core.admin import BaseModelAdmin
from linkedin.models import HTTPProxy, LinkedinAccount


@admin.register(HTTPProxy)
class HTTPProxyAdmin(BaseModelAdmin):
    list_display = ["id", "link", "is_active"]
    list_display_links = ["id", "link"]
    ordering = ["-is_active", "-id"]


@admin.register(LinkedinAccount)
class LinkedinAccountAdmin(BaseModelAdmin):
    list_display = ["username", "is_active"]
    ordering = ["-is_active", "-id"]
