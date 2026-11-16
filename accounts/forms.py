from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class EmailUniquenessMixin:
    """Case-insensitive unique email check (BR-02)."""

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        clash = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class RegistrationForm(EmailUniquenessMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("full_name", "username", "email", "contact_number")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].widget.attrs.update(autofocus=True, autocomplete="name")
        self.fields["username"].help_text = "Letters, digits and @/./+/-/_ only."
        self.fields["email"].widget.attrs.update(autocomplete="email")
        self.fields["contact_number"].widget.attrs.update(autocomplete="tel")
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm password"
        self.fields["password2"].help_text = "Type the same password again."
        self.error_messages["password_mismatch"] = "The two passwords do not match."

    def save(self, commit=True):
        user = super().save(commit=False)
        # The first account created becomes the Owner so the shop always has
        # one (BR-08). Everyone who registers after that starts as Staff; an
        # Owner can change roles later (BR-05).
        has_owner = User.objects.filter(role=User.Role.OWNER).exists()
        user.role = User.Role.STAFF if has_owner else User.Role.OWNER
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": (
            "Incorrect username or password, or this account is deactivated. "
            "Check your details and try again."
        ),
        "inactive": "This account is deactivated.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(autofocus=True, autocomplete="username")
        self.fields["password"].widget.attrs.update(autocomplete="current-password")


class ProfileForm(EmailUniquenessMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("full_name", "email", "contact_number", "profile_photo")

