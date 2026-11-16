from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Require a logged-in user whose role is one of `roles`.

    Logged-out users are sent to the login page; logged-in users with the
    wrong role get a 403 page, so typing another role's URL never works.
    """

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied("Your role cannot open this page.")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
