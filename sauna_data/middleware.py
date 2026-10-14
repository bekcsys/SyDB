from django.db import IntegrityError
from django.db.utils import DataError
from django.shortcuts import render


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
