from django.db import IntegrityError
from django.db.utils import DataError
from django.http import JsonResponse
from django.shortcuts import redirect, render


class SaunaLoginMiddleware:
    """The knowledge base and its files stay behind a login. Admin keeps its own login."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated or self._is_public(request.path):
            return self.get_response(request)
        if request.path.startswith("/api/"):
            return JsonResponse({"error": "Login required."}, status=401)
        return redirect(f"/login/?next={request.get_full_path()}")

    @staticmethod
    def _is_public(path: str) -> bool:
        return path.startswith(("/login/", "/admin/", "/static/"))


class FriendlyDatabaseErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, (IntegrityError, DataError)):
            return None
        return render(
            request,
            "sauna_data/friendly_error.html",
            {
                "message": (
                    "That change could not be saved. Please check your entries "
                    "and try again."
                )
            },
            status=400,
        )
