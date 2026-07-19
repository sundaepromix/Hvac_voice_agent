"""Tests for phone normalization, digit-tail matching, and the DB cleanup command."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.calls.services.persistence import upsert_customer
from apps.core.models import Business
from apps.leads.models import Customer, Lead
from apps.leads.phones import find_customer_by_phone, normalize_phone, phone_tail


class NormalizePhoneTests(TestCase):
    def test_formats(self):
        self.assertEqual(normalize_phone("+1 (555) 123-4567"), "+15551234567")
        self.assertEqual(normalize_phone("0812 345 6789"), "08123456789")
        self.assertEqual(normalize_phone("002348123456789"), "+2348123456789")
        self.assertEqual(normalize_phone("+2349126639036"), "+2349126639036")
        self.assertEqual(normalize_phone("  "), "")
        self.assertEqual(normalize_phone(None), "")

    def test_tail(self):
        self.assertEqual(phone_tail("+2348147805024"), "8147805024")
        self.assertEqual(phone_tail("08147805024"), "8147805024")


class FindCustomerByPhoneTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Acme", slug="acme")

    def test_matches_across_formats_both_directions(self):
        cust = Customer.objects.create(
            business=self.business, name="Francis", phone="08147805024")
        self.assertEqual(
            find_customer_by_phone(self.business, "+2348147805024"), cust)
        cust.phone = "+2348147805024"
        cust.save()
        self.assertEqual(
            find_customer_by_phone(self.business, "0814 780 5024"), cust)

    def test_no_match_on_different_numbers(self):
        Customer.objects.create(
            business=self.business, name="Safe", phone="+2341266639036")
        self.assertIsNone(find_customer_by_phone(self.business, "+2349126639036"))


class UpsertCustomerNormalizationTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Acme", slug="acme")

    def test_local_then_international_is_one_customer(self):
        first = upsert_customer(self.business, name="Francis", phone="08147805024")
        second = upsert_customer(self.business, phone="+2348147805024")
        self.assertEqual(first.id, second.id)
        self.assertEqual(Customer.objects.count(), 1)
        second.refresh_from_db()
        self.assertEqual(second.phone, "+2348147805024")

    def test_phone_stored_normalized(self):
        cust = upsert_customer(self.business, name="Jane", phone="+1 (555) 123-4567")
        self.assertEqual(cust.phone, "+15551234567")


class NormalizePhonesCommandTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Acme", slug="acme")

    def _run(self, *args):
        out = StringIO()
        call_command("normalize_phones", *args, stdout=out)
        return out.getvalue()

    def test_merges_duplicates_and_moves_leads(self):
        keeper = Customer.objects.create(
            business=self.business, name="Francis", phone="+2348147805024")
        dup = Customer.objects.create(
            business=self.business, phone="08147805024", address="12 Maple St")
        Lead.objects.create(business=self.business, customer=keeper, project_summary="AC fix")
        Lead.objects.create(business=self.business, customer=dup, project_summary="Roof leak")

        out = self._run()
        self.assertIn("merge", out)
        self.assertEqual(Customer.objects.count(), 1)
        survivor = Customer.objects.get()
        self.assertEqual(survivor.id, keeper.id)
        self.assertEqual(survivor.leads.count(), 2)
        self.assertEqual(survivor.address, "12 Maple St")

    def test_normalizes_formats(self):
        cust = Customer.objects.create(
            business=self.business, name="Jane", phone="+1 (555) 123-4567")
        self._run()
        cust.refresh_from_db()
        self.assertEqual(cust.phone, "+15551234567")

    def test_dry_run_changes_nothing(self):
        Customer.objects.create(business=self.business, phone="+2348147805024")
        Customer.objects.create(business=self.business, phone="08147805024")
        out = self._run("--dry-run")
        self.assertIn("DRY RUN", out)
        self.assertEqual(Customer.objects.count(), 2)

    def test_different_numbers_never_merge(self):
        Customer.objects.create(business=self.business, name="Safe", phone="+2341266639036")
        Customer.objects.create(business=self.business, name="Maxwell", phone="+2349126639036")
        self._run()
        self.assertEqual(Customer.objects.count(), 2)
