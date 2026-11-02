from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        response.data = {
            "error": {
                "code": "validation_error",
                "message": "Les données fournies sont invalides.",
                "details": response.data,
            }
        }
        return response

    if isinstance(response.data, dict):
        detail = response.data.get("detail", response.data)
    else:
        detail = response.data
    error_code = getattr(
        detail,
        "code",
        getattr(exc, "default_code", "api_error"),
    )
    response.data = {
        "error": {
            "code": str(error_code),
            "message": str(detail),
            "details": None,
        }
    }
    return response
