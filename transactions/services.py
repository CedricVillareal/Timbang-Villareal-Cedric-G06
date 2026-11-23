from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from .models import Transaction, TransactionItem

TWO_PLACES = Decimal("0.01")


def next_transaction_no(date):
    prefix = f"TXN-{date:%Y%m%d}-"
    last = (
        Transaction.objects.filter(transaction_no__startswith=prefix)
        .order_by("-transaction_no")
        .first()
    )
    number = int(last.transaction_no[-4:]) + 1 if last else 1
    return f"{prefix}{number:04d}"


@transaction.atomic
def record_transaction(*, user, seller, date, items):
    """Save a purchase and its lines in one database transaction.

    `items` is a list of (material, quantity). Each line's unit price is the
    material's current price, copied onto the line so later price changes never
    alter it (BR-19). Subtotals and the total are computed here (BR-20).
    """
    today = timezone.localdate()
    txn = Transaction.objects.create(
        transaction_no=next_transaction_no(date),
        seller=seller,
        recorded_by=user,
        transaction_date=date,
        total_amount=Decimal("0.00"),
    )
    total = Decimal("0.00")
    for material, quantity in items:
        price = material.price_on(today)
        if price is None:
            raise ValueError(f"{material.name} has no current price.")
        subtotal = (quantity * price.price_per_unit).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        TransactionItem.objects.create(
            transaction=txn,
            material=material,
            price=price,
            quantity=quantity,
            unit_price=price.price_per_unit,
            subtotal=subtotal,
        )
        total += subtotal
    txn.total_amount = total
    txn.save(update_fields=["total_amount"])
    return txn


@transaction.atomic
def void_transaction(*, txn, user, reason):
    """Void a completed transaction once, with a reason (BR-22, BR-23)."""
    locked = Transaction.objects.select_for_update().get(pk=txn.pk)
    if locked.status == Transaction.Status.VOIDED:
        raise ValueError("This transaction has already been voided.")
    locked.status = Transaction.Status.VOIDED
    locked.voided_by = user
    locked.voided_at = timezone.now()
    locked.void_reason = reason
    locked.save(update_fields=["status", "voided_by", "voided_at", "void_reason"])
    return locked