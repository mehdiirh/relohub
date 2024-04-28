from base64 import b64decode
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase

from core.utils import (
    get_random_hex,
    remove_exponent,
    from_global_id,
    to_global_id,
    intcomma_decorator,
)
from user.models import User


class UtilsTestCase(TestCase):

    def test_get_random_hex(self):
        hex_value = get_random_hex()
        self.assertIsInstance(hex_value, str, "Returned value should be a string")
        self.assertEqual(
            len(hex_value), 32, "Length of hex value should be 32 characters"
        )
        self.assertTrue(
            all(c in "0123456789abcdef" for c in hex_value),
            "Hex value should only contain hexadecimal characters",
        )

        results = set()
        for _ in range(100):  # Test 100 times
            result = get_random_hex()
            results.add(result)

        self.assertEqual(len(results), 100, "Generated hex values should be unique")

    def test_remove_exponent(self):
        result = remove_exponent(6500.00000)
        self.assertIsInstance(result, Decimal, "Returned value should be a Decimal")
        self.assertEqual(result, Decimal("6500"), "Extra zeros should be removed")

        result = remove_exponent(-6500.00000)
        self.assertEqual(
            result,
            Decimal("-6500"),
            "Extra zeros should be removed from negative numbers",
        )

        result = remove_exponent(6500)
        self.assertEqual(result, Decimal("6500"), "Integer should not be changed")

    def test_intcomma_decorator(self):

        @intcomma_decorator()
        def _intcomma_function(number):
            return number

        @intcomma_decorator(prefix="PREFIXED")
        def _intcomma_prefix_function(number):
            return number

        @intcomma_decorator(suffix="SUFFIXED")
        def _intcomma_suffix_function(number):
            return number

        @intcomma_decorator(prefix="PREFIXED", suffix="SUFFIXED")
        def _intcomma_prefix_suffix_function(number):
            return number

        result = _intcomma_function(100)
        self.assertEqual(result, "100")

        result = _intcomma_function(1000)
        self.assertEqual(result, "1,000")

        result = _intcomma_function(1000000)
        self.assertEqual(result, "1,000,000")

        result = _intcomma_function(Decimal("1000"))
        self.assertEqual(result, "1,000")

        result = _intcomma_function(1000.55)
        self.assertEqual(result, "1,000.55")

        result = _intcomma_function(Decimal("1000.55"))
        self.assertEqual(result, "1,000.55")

        result = _intcomma_function(None)
        self.assertEqual(result, "None")

        # test with prefix
        result = _intcomma_prefix_function(1000)
        self.assertEqual(result, "PREFIXED1,000")

        # test with suffix
        result = _intcomma_suffix_function(1000)
        self.assertEqual(result, "1,000SUFFIXED")

        # test with prefix
        result = _intcomma_prefix_suffix_function(1000)
        self.assertEqual(result, "PREFIXED1,000SUFFIXED")


class GlobalIDTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(id=1, username="test_user")
        self.group = Group.objects.create(id=1, name="test_group")

    def test_return_none_on_invalid_global_id(self):
        result = from_global_id("invalid_id")
        self.assertIsNone(result)

    def test_return_none_on_invalid_model_type(self):
        global_id = "VXNlcjox"  # 'User:1'
        result = from_global_id(global_id, model=Group, raise_error=False)
        self.assertIsNone(result)

    def test_return_pk_only(self):
        global_id = "VXNlcjox"  # 'User:1'
        result = from_global_id(global_id, return_pk_only=True)
        self.assertEqual(result, 1)

    def test_return_instance(self):
        global_id = "VXNlcjox"  # 'User:1'
        result = from_global_id(global_id, model=User)
        self.assertEqual(result, self.user)

    def test_raise_error_on_invalid_global_id(self):
        with self.assertRaises(ValueError):
            from_global_id("invalid_id", raise_error=True)

    def test_raise_error_on_invalid_model_type(self):
        global_id = "VXNlcjox"  # 'User:1'
        with self.assertRaises(ValueError):
            from_global_id(global_id, model="Group", raise_error=True)

    def test_raise_error_on_object_does_not_exist(self):
        global_id = "VXNlcjoy"  # 'User:2'
        with self.assertRaises(ValueError):
            from_global_id(global_id, model=User, raise_error=True)

    def test_to_global_id(self):
        global_id = to_global_id(self.user)
        self.assertIsInstance(global_id, str, "Returned value should be a string")

        instance = from_global_id(global_id, model=User)
        self.assertEqual(
            instance, self.user, "Decoded instance should match the original instance"
        )

        class_name, pk = b64decode(global_id).decode().split(":")
        self.assertEqual(
            class_name, "User", "Class name in global ID should match model name"
        )
        self.assertEqual(
            int(pk),
            self.user.pk,
            "Primary key in global ID should match instance's primary key",
        )

    def test_to_global_id_different_instances(self):
        global_id_user = to_global_id(self.user)
        global_id_group = to_global_id(self.group)
        self.assertNotEqual(
            global_id_user,
            global_id_group,
            "Global IDs for different instances should be different",
        )
