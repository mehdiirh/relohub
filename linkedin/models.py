from django.db import models
from django.utils.translation import gettext_lazy as _
from linkedin_api import Linkedin
from requests.cookies import cookiejar_from_dict

from core.models import ModelWithMetadata


class HTTPProxy(ModelWithMetadata):
    class Meta:
        verbose_name = _("HTTP Proxy")
        verbose_name_plural = _("HTTP Proxies")

    host = models.CharField(_("host"), max_length=128)
    port = models.IntegerField(_("port"))
    username = models.CharField(_("username"), max_length=64, null=True, blank=True)
    password = models.CharField(_("password"), max_length=64, null=True, blank=True)

    def __str__(self):
        return self.link

    @property
    def link(self):
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"

    @property
    def link_dict(self):
        return {"http": self.link, "https": self.link}


class LinkedinAccount(ModelWithMetadata):
    class Meta:
        verbose_name = _("Linkedin Account")
        verbose_name_plural = _("Linkedin Accounts")

    username = models.CharField(
        _("username"), max_length=128, unique=True, db_index=True
    )
    password = models.CharField(_("password"), max_length=256)
    cookies = models.JSONField(_("cookies"), null=True, blank=True)
    last_used = models.DateTimeField(_("last used"))
    proxy = models.ForeignKey(
        verbose_name=_("proxy"),
        to=HTTPProxy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.username} #{self.pk}"

    @property
    def client(self):
        if proxy := self.proxy:
            proxy = proxy.link_dict

        if cookies := self.cookies:
            cookies = cookiejar_from_dict(self.cookies)

        client = Linkedin(
            self.username,
            self.password,
            proxies=proxy or {},
            cookies=cookies,
        )

        self.cookies = dict(client._cookies())
        self.save()

        return client
