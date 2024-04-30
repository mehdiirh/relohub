from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import redirect, reverse
from django.utils.deprecation import MiddlewareMixin


class ForceDefaultAdminToChangePassword(MiddlewareMixin):
    """
    Middleware to force default admin to change their password
    """

    @staticmethod
    def process_request(request: HttpRequest):
        if not request.user.is_superuser:
            return

        destination = reverse("admin:password_change")

        if request.user.check_password("(#ChangeMe!)") and not request.path.startswith(
            destination
        ):
            messages.warning(
                request, "First things first! Please change your password."
            )
            return redirect(destination)
