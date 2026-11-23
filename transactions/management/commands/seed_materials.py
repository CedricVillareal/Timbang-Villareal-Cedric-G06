from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from transactions.models import Material, MaterialPrice

User = get_user_model()

STARTER = [
    ("Carton", "PAPER", "KG", "3.00"),
    ("Newspaper", "PAPER", "KG", "4.00"),
    ("PET Bottles", "PLASTIC", "KG", "12.00"),
    ("Aluminum Cans", "METAL", "KG", "60.00"),
    ("Copper", "METAL", "KG", "350.00"),
    ("Glass Bottles", "GLASS", "PC", "1.00"),
]


class Command(BaseCommand):
    help = "Create starter materials and prices. Safe to run more than once."

    def handle(self, *args, **options):
        owner = User.objects.filter(role=User.Role.OWNER).order_by("id").first()
        if owner is None:
            raise CommandError("Register an Owner account first, then run this command again.")
        today = timezone.localdate()
        for name, category, unit, price in STARTER:
            material, created = Material.objects.get_or_create(
                name=name, defaults={"category": category, "unit": unit}
            )
            if not material.prices.exists():
                MaterialPrice.objects.create(
                    material=material, price_per_unit=Decimal(price), effective_from=today, set_by=owner
                )
            self.stdout.write(f"{'Created' if created else 'Exists'}: {name}")
        self.stdout.write(self.style.SUCCESS("Starter materials are ready."))