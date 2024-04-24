from base64 import b64decode, b64encode
from decimal import Decimal
from functools import wraps
from hashlib import md5
from typing import Union

from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone


def get_random_hex():
    """
    Generates a random hex value

    Returns:
        str: hex
    """

    now = str(timezone.now().timestamp()).encode()
    hex_value = md5(str(now).encode()).hexdigest()
    return hex_value


def to_global_id(instance) -> str:
    """
    Resolves `instance` to its global id.

    Args:
        instance: instance of a model

    Returns:
        str: global id of instance
    """

    class_name = instance.__class__.__name__
    class_pk = instance.pk
    keyword = f"{class_name}:{class_pk}".encode()
    return b64encode(keyword).decode()


def from_global_id(
    global_id: str,
    model: Union[str, models.Model] = None,
    return_pk_only=False,
    raise_error=False,
):
    """
    Resolves global id to instance or pk of object

    Args:
        global_id: global id to be resolved
        model: model object or name
        return_pk_only: if True, object's instance will not be resolved,
         and only it's primary key will be returned
        raise_error: if False, all errors will be muted and returns "None"

    Returns:
        Union[None, int, object]: pk or instance or None

    Raises:
        ValueError: if there's any error
    """

    try:
        keyword = b64decode(global_id.encode())
        content_type, pk = keyword.decode().split(":")
        pk = int(pk)
    except:
        if raise_error:
            raise ValueError("invalid global id")
        return

    content_type = content_type.lower()
    if model:
        if isinstance(model, str):
            if content_type != model:
                if raise_error:
                    raise ValueError("invalid model type")
                return
        if issubclass(model, models.Model):
            if content_type != model._meta.model_name:
                if raise_error:
                    raise ValueError("invalid model type")
                return
        else:
            if raise_error:
                raise ValueError("invalid model type")
            return

    if return_pk_only:
        return pk

    ct = ContentType.objects.get(model=content_type)
    try:
        instance = ct.model_class().objects.get(pk=pk)
    except ObjectDoesNotExist:
        if raise_error:
            raise ValueError("object does not exists")
        return

    return instance


def remove_exponent(number: Union[Decimal, int, float]) -> Decimal:
    """
    Remove extra zeros from decimal value. like: `6500.00000` -> `6500`

    Args:
        number: decimal number

    Returns:
        Decimal: corrected value
    """

    if isinstance(number, int):
        number = Decimal(number)
    if isinstance(number, float):
        number = Decimal(str(number))

    normalized_num = (
        number.to_integral() if number == number.to_integral() else number.normalize()
    )

    return normalized_num


def remove_exponent_decorator(fn: callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        number = fn(*args, **kwargs)
        normalized_num = remove_exponent(number)
        return str(normalized_num)

    return wrapper


def intcomma_decorator(prefix="", suffix=""):
    def inner(fn: callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            number = fn(*args, **kwargs)
            intcomma_num = intcomma(number)
            return f"{prefix}{intcomma_num}{suffix}"

        return wrapper

    return inner
