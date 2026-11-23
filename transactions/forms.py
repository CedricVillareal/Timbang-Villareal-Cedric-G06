import re
from decimal import Decimal

from django import forms
from django.forms import BaseFormSet, formset_factory
from django.utils import timezone

from .models import Material, Seller


class SellerForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ("full_name", "contact_number", "address", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def clean_full_name(self):
        return self.cleaned_data["full_name"].strip()

    def clean_contact_number(self):
        number = (self.cleaned_data.get("contact_number") or "").strip()
        if not number:
            return None  # optional; NULL keeps the unique rule from clashing (BR-09)
        if not re.fullmatch(r"[0-9+\-\s()]{7,20}", number):
            raise forms.ValidationError("Enter a valid contact number (7 to 20 digits, spaces, + or -).")
        return number


class TransactionForm(forms.Form):
    seller = forms.ModelChoiceField(
        queryset=Seller.objects.filter(status=Seller.Status.ACTIVE),  # BR-11
        empty_label="Select a seller",
    )
    transaction_date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def clean_transaction_date(self):
        date = self.cleaned_data["transaction_date"]
        if date > timezone.localdate():
            raise forms.ValidationError("The transaction date cannot be in the future.")  # BR-24
        return date


class ItemForm(forms.Form):
    material = forms.ModelChoiceField(
        queryset=Material.objects.filter(status=Material.Status.ACTIVE),  # BR-13
        empty_label="Select a material",
    )
    quantity = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01"),  # BR-18
        error_messages={"min_value": "Quantity must be greater than zero."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["material"].label_from_instance = lambda m: f"{m.name} ({m.get_unit_display()})"

    def clean_material(self):
        material = self.cleaned_data["material"]
        if material.price_on(timezone.localdate()) is None:  # BR-16
            raise forms.ValidationError(f"{material.name} has no current price yet.")
        return material


class BaseItemFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        seen = set()
        for form in self.forms:
            data = form.cleaned_data
            if not data:
                continue  # blank extra row
            if data["material"].pk in seen:
                raise forms.ValidationError("Each material can appear only once per transaction.")  # BR-21
            seen.add(data["material"].pk)
        if not seen:
            raise forms.ValidationError("Add at least one material with a quantity.")  # BR-17


ItemFormSet = formset_factory(ItemForm, formset=BaseItemFormSet, extra=5)


class VoidForm(forms.Form):
    reason = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={"rows": 3}),
        error_messages={"required": "A reason is required to void a transaction."},  # BR-22
    )

    def clean_reason(self):
        return self.cleaned_data["reason"].strip()