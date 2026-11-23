from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Seller(models.Model):
    """A person who sells recyclables to the junkshop (SDD: sellers)."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    full_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, unique=True, null=True, blank=True)  # BR-09
    address = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sellers_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class Material(models.Model):
    """A recyclable material the shop buys (SDD: materials)."""

    class Category(models.TextChoices):
        PAPER = "PAPER", "Paper"
        PLASTIC = "PLASTIC", "Plastic"
        METAL = "METAL", "Metal"
        GLASS = "GLASS", "Glass"
        OTHER = "OTHER", "Other"

    class Unit(models.TextChoices):
        KG = "KG", "kg"
        PC = "PC", "piece"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    name = models.CharField(max_length=80, unique=True)  # BR-12
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    unit = models.CharField(max_length=5, choices=Unit.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def price_on(self, date):
        """The price record in effect on `date`, or None (BR-15, BR-16)."""
        return (
            self.prices.filter(effective_from__lte=date)
            .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=date))
            .order_by("-effective_from")
            .first()
        )

    @property
    def current_price(self):
        return self.price_on(timezone.localdate())


class MaterialPrice(models.Model):
    """Buying price history for a material (SDD: material_prices)."""

    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="prices")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="prices_set"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["material__name", "-effective_from"]
        constraints = [
            models.CheckConstraint(condition=Q(price_per_unit__gt=0), name="price_gt_zero"),  # BR-14
            models.UniqueConstraint(fields=["material", "effective_from"], name="unique_price_start"),
        ]

    def __str__(self):
        return f"{self.material} {self.price_per_unit} from {self.effective_from}"


class Transaction(models.Model):
    """One purchase from one seller (SDD: transactions)."""

    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        VOIDED = "VOIDED", "Voided"

    transaction_no = models.CharField(max_length=20, unique=True)
    seller = models.ForeignKey(Seller, on_delete=models.PROTECT, related_name="transactions")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transactions_recorded"
    )
    transaction_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="transactions_voided",
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(condition=Q(total_amount__gte=0), name="txn_total_gte_zero"),
            # A voided transaction must say who voided it, when, and why (BR-22).
            models.CheckConstraint(
                condition=Q(status="COMPLETED")
                | (Q(voided_by__isnull=False) & Q(voided_at__isnull=False) & Q(void_reason__isnull=False)),
                name="txn_void_fields_required",
            ),
        ]

    def __str__(self):
        return self.transaction_no


class TransactionItem(models.Model):
    """A material line on a transaction (SDD: transaction_items)."""

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="items")
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="transaction_items")
    price = models.ForeignKey(MaterialPrice, on_delete=models.PROTECT, related_name="transaction_items")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot (BR-19)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="item_qty_gt_zero"),  # BR-18
            models.CheckConstraint(condition=Q(unit_price__gt=0), name="item_unit_price_gt_zero"),
            models.UniqueConstraint(fields=["transaction", "material"], name="one_material_per_txn"),  # BR-21
        ]

    def __str__(self):
        return f"{self.transaction} - {self.material}"