from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import role_required

from .forms import ItemFormSet, SellerForm, TransactionForm, VoidForm
from .models import Material, Seller, Transaction
from .services import record_transaction, void_transaction

User = get_user_model()
BOTH_ROLES = (User.Role.OWNER, User.Role.STAFF)


def visible_transactions(user):
    """Owners see every transaction; Staff see only the ones they recorded."""
    qs = Transaction.objects.select_related("seller", "recorded_by")
    return qs if user.is_owner else qs.filter(recorded_by=user)




@role_required(*BOTH_ROLES)
def seller_list(request):
    sellers = Seller.objects.select_related("created_by")
    return render(request, "transactions/seller_list.html", {"sellers": sellers})


@role_required(*BOTH_ROLES)
def seller_create(request):
    if request.method == "POST":
        form = SellerForm(request.POST)
        if form.is_valid():
            seller = form.save(commit=False)
            seller.created_by = request.user
            seller.save()
            messages.success(request, f"Seller {seller.full_name} was added.")
            return redirect("transactions:seller_list")
        messages.error(request, "The seller was not saved. Fix the fields marked below.")
    else:
        form = SellerForm()
    return render(request, "transactions/seller_form.html", {"form": form})




@role_required(*BOTH_ROLES)
def transaction_list(request):
    transactions = visible_transactions(request.user)
    return render(request, "transactions/transaction_list.html", {"transactions": transactions})


@role_required(*BOTH_ROLES)
def transaction_create(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        formset = ItemFormSet(request.POST, prefix="items")
        valid = form.is_valid()
        valid = formset.is_valid() and valid
        if valid:
            items = [
                (f.cleaned_data["material"], f.cleaned_data["quantity"])
                for f in formset.forms
                if f.cleaned_data
            ]
            try:
                txn = record_transaction(
                    user=request.user,
                    seller=form.cleaned_data["seller"],
                    date=form.cleaned_data["transaction_date"],
                    items=items,
                )
            except ValueError as error:
                messages.error(request, str(error))
            else:
                messages.success(
                    request, f"Transaction {txn.transaction_no} was saved. Total payable: PHP {txn.total_amount:,.2f}."
                )
                return redirect("transactions:detail", pk=txn.pk)
        else:
            messages.error(request, "The transaction was not saved. Fix the problems marked below.")
    else:
        form = TransactionForm()
        formset = ItemFormSet(prefix="items")

    today = timezone.localdate()
    prices = [(m, m.price_on(today)) for m in Material.objects.filter(status=Material.Status.ACTIVE)]
    return render(
        request,
        "transactions/transaction_form.html",
        {"form": form, "formset": formset, "prices": prices},
    )


def _render_detail(request, txn, void_form):
    return render(request, "transactions/transaction_detail.html", {"txn": txn, "void_form": void_form})


@role_required(*BOTH_ROLES)
def transaction_detail(request, pk):
    txn = get_object_or_404(visible_transactions(request.user).prefetch_related("items__material"), pk=pk)
    return _render_detail(request, txn, VoidForm())


@role_required(User.Role.OWNER)
@require_POST
def transaction_void(request, pk):
    txn = get_object_or_404(visible_transactions(request.user).prefetch_related("items__material"), pk=pk)
    form = VoidForm(request.POST)
    if form.is_valid():
        try:
            void_transaction(txn=txn, user=request.user, reason=form.cleaned_data["reason"])
        except ValueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"Transaction {txn.transaction_no} was voided.")
        return redirect("transactions:detail", pk=txn.pk)
    messages.error(request, "The transaction was not voided. A reason is required.")
    return _render_detail(request, txn, form)