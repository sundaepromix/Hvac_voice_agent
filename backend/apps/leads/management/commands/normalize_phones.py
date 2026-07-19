"""Normalize stored customer phone numbers and merge duplicate customers.

One-off cleanup + safe to re-run: rewrites every Customer.phone to the
canonical format from apps.leads.phones, then merges customers in the same
business that are the same person under different formats (matched on the
normalized last 10 digits). Leads move to the surviving row, missing contact
fields are filled from the duplicates, and the duplicates are deleted.

Run with --dry-run first to see what would change.
"""
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Business
from apps.leads.models import Customer
from apps.leads.phones import normalize_phone, phone_tail


class Command(BaseCommand):
    help = "Normalize customer phone formats and merge duplicates that share a number."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Report what would change without writing anything.")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        normalized = merged = 0

        with transaction.atomic():
            for business in Business.objects.all():
                normalized += self._normalize_formats(business, dry)
                merged += self._merge_duplicates(business, dry)
            if dry:
                transaction.set_rollback(True)

        mode = "DRY RUN — nothing written" if dry else "applied"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: {normalized} phone(s) normalized, {merged} duplicate customer(s) merged."
        ))

    def _normalize_formats(self, business, dry: bool) -> int:
        count = 0
        for cust in Customer.objects.filter(business=business).exclude(phone=""):
            canonical = normalize_phone(cust.phone)
            if canonical != cust.phone:
                self.stdout.write(
                    f"  normalize customer #{cust.id}: {cust.phone!r} -> {canonical!r}"
                )
                cust.phone = canonical
                if not dry:
                    cust.save(update_fields=["phone"])
                count += 1
        return count

    def _merge_duplicates(self, business, dry: bool) -> int:
        groups: dict[str, list[Customer]] = defaultdict(list)
        for cust in Customer.objects.filter(business=business).exclude(phone="").order_by("id"):
            tail = phone_tail(cust.phone)
            if len(tail) >= 7:
                groups[tail].append(cust)

        merged = 0
        for tail, dupes in groups.items():
            if len(dupes) < 2:
                continue
            keeper = self._pick_keeper(dupes)
            for dup in dupes:
                if dup.id == keeper.id:
                    continue
                self.stdout.write(
                    f"  merge customer #{dup.id} ({dup.phone!r}, {dup.name or '-'}) "
                    f"-> #{keeper.id} ({keeper.phone!r}, {keeper.name or '-'}) "
                    f"[{dup.leads.count()} lead(s) moved]"
                )
                if not dry:
                    dup.leads.update(customer=keeper)
                    dirty = []
                    for field in ("name", "email", "address", "notes"):
                        if not getattr(keeper, field) and getattr(dup, field):
                            setattr(keeper, field, getattr(dup, field))
                            dirty.append(field)
                    if not keeper.phone.startswith("+") and dup.phone.startswith("+"):
                        keeper.phone = dup.phone
                        dirty.append("phone")
                    if dirty:
                        keeper.save(update_fields=dirty)
                    dup.delete()
                merged += 1
        return merged

    @staticmethod
    def _pick_keeper(dupes: list[Customer]) -> Customer:
        # Prefer the row with a full international number, then the one with
        # the most history, then the oldest.
        return sorted(
            dupes,
            key=lambda c: (not c.phone.startswith("+"), -c.leads.count(), c.id),
        )[0]
