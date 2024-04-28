from django.test import TestCase

from linkedin.models import HTTPProxy


# noinspection HttpUrlsUsage
class HTTPProxyModelTest(TestCase):

    def test_link_property_without_username_and_password(self):
        proxy = HTTPProxy(host="example.com", port=8080)
        self.assertEqual(
            proxy.link,
            "http://example.com:8080",
        )

    def test_link_property_with_username_and_password(self):
        proxy = HTTPProxy(
            host="example.com", port=8080, username="user", password="pass"
        )
        self.assertEqual(
            proxy.link,
            "http://user:pass@example.com:8080",
        )

    def test_link_dict_property_without_username_and_password(self):
        proxy = HTTPProxy(host="example.com", port=8080)
        self.assertEqual(
            proxy.link_dict,
            {
                "http": "http://example.com:8080",
                "https": "http://example.com:8080",
            },
        )

    def test_link_dict_property_with_username_and_password(self):
        proxy = HTTPProxy(
            host="example.com", port=8080, username="user", password="pass"
        )
        self.assertEqual(
            proxy.link_dict,
            {
                "http": "http://user:pass@example.com:8080",
                "https": "http://user:pass@example.com:8080",
            },
        )
