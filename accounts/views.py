from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from transactions.models import Transaction

from .decorators import role_required
from .forms import LoginForm, ProfileForm, RegistrationForm

User = get_user_model()


def home(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return redirect("accounts:login")


# --- Registration, login, logout -------------------------------------------

def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Account created. You are registered as {user.get_role_display()}. "
                "Log in to continue.",
            )
            return redirect("accounts:login")
        messages.error(
            request, "We could not create your account. Fix the fields marked below and try again."
        )
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


class TimbangLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().get_short_name()}.")
        return super().form_valid(form)


@require_POST
def logout_view(request):
    logout(request)  # ends the session
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


# --- Role-based dashboards ---------------------------------------------------

@login_required
def dashboard(request):
    """Send each user to the dashboard for their role."""
    return redirect(request.user.dashboard_url_name)


@role_required(User.Role.OWNER)
def owner_dashboard(request):
    recent = Transaction.objects.select_related("seller", "recorded_by")[:5]
    return render(request, "dashboards/owner.html", {"recent": recent})


@role_required(User.Role.STAFF)
def staff_dashboard(request):
    recent = Transaction.objects.select_related("seller").filter(recorded_by=request.user)[:5]
    return render(request, "dashboards/staff.html", {"recent": recent})

# --- Profile (always the signed-in user's own record) -----------------------

@login_required
def profile(request):
    return render(request, "accounts/profile.html")


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
        messages.error(request, "Profile not saved. Fix the fields marked below.")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile_edit.html", {"form": form})
