"""Tests for returning-caller memory — the known_caller_block prompt builder."""
from django.core.cache import cache
from django.test import TestCase

from apps.calls.services.caller_memory import known_caller_block
from apps.core.models import Business
from apps.leads.models import Customer, Lead
from apps.quotes.models import Quote


class KnownCallerBlockTests(TestCase):
    def setUp(self):
        cache.clear()
        self.business = Business.objects.create(name="Acme HVAC", slug="acme")
        self.customer = Customer.objects.create(
            business=self.business,
            name="Mark Johnson",
            phone="+15551234567",
            address="12 Maple Street, Austin",
        )

    def _lead(self, summary="Water heater replacement", status="quoted", **extracted):
        return Lead.objects.create(
            business=self.business,
            customer=self.customer,
            project_summary=summary,
            status=status,
            extracted_fields=extracted,
        )

    def test_unknown_phone_returns_empty(self):
        self.assertEqual(known_caller_block(self.business, "+19998887777"), "")

    def test_known_caller_with_history(self):
        self._lead(vapi_call_id="call-monday")
        block = known_caller_block(self.business, "+15551234567", call_id="call-tuesday")
        self.assertIn("RETURNING CALLER", block)
        self.assertIn("Mark Johnson", block)
        self.assertIn("Water heater replacement", block)
        self.assertIn("quoted", block)

    def test_current_calls_own_lead_is_not_history(self):
        self._lead(summary="Live call in progress", vapi_call_id="call-now")
        block = known_caller_block(self.business, "+15551234567", call_id="call-now")
        self.assertNotIn("Live call in progress", block)

    def test_lead_without_vapi_call_id_still_counts(self):
        self._lead(summary="Chat widget inquiry")
        block = known_caller_block(self.business, "+15551234567", call_id="call-now")
        self.assertIn("Chat widget inquiry", block)

    def test_matches_on_last_digits_when_format_differs(self):
        self._lead(vapi_call_id="call-old")
        self.customer.phone = "(555) 123-4567"
        self.customer.save()
        block = known_caller_block(self.business, "+15551234567", call_id="call-new")
        self.assertIn("Mark Johnson", block)

    def test_latest_quote_is_mentioned(self):
        lead = self._lead(vapi_call_id="call-old")
        Quote.objects.create(lead=lead, reference="HL-TEST01", total=1850, subtotal=1850)
        block = known_caller_block(self.business, "+15551234567", call_id="call-new")
        self.assertIn("HL-TEST01", block)

    def test_upcoming_booking_is_mentioned_but_past_is_not(self):
        self._lead(
            summary="Past job", status="won", vapi_call_id="call-a",
            booking={"date": "2020-01-05", "time": "09:00"},
        )
        block = known_caller_block(self.business, "+15551234567", call_id="call-new")
        self.assertNotIn("Upcoming appointment", block)

        self._lead(
            summary="Booked job", status="booked", vapi_call_id="call-b",
            booking={"date": "2099-06-01", "time": "10:00"},
        )
        cache.clear()
        block = known_caller_block(self.business, "+15551234567", call_id="call-new2")
        self.assertIn("Upcoming appointment", block)
        self.assertIn("June 01", block)

    def test_snapshot_is_cached_per_call(self):
        self._lead(summary="First job", vapi_call_id="call-old")
        first = known_caller_block(self.business, "+15551234567", call_id="call-live")
        self._lead(summary="Mid-call surprise", vapi_call_id="call-other")
        second = known_caller_block(self.business, "+15551234567", call_id="call-live")
        self.assertEqual(first, second)
        self.assertNotIn("Mid-call surprise", second)

    def test_customer_without_past_leads_is_not_welcomed_back(self):
        # A customer row alone (e.g. created earlier in THIS call by
        # qualify_lead) must never trigger the returning-caller greeting.
        block = known_caller_block(self.business, "+15551234567", call_id="call-first")
        self.assertEqual(block, "")

        self._lead(summary="Live call in progress", vapi_call_id="call-first")
        cache.clear()
        block = known_caller_block(self.business, "+15551234567", call_id="call-first")
        self.assertEqual(block, "")

    def test_missing_phone_or_business(self):
        self.assertEqual(known_caller_block(self.business, None), "")
        self.assertEqual(known_caller_block(self.business, "   "), "")
        self.assertEqual(known_caller_block(None, "+15551234567"), "")
