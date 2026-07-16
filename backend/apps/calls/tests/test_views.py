"""Smoke tests for the Vapi-facing webhook + custom-LLM endpoints."""
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.core.models import Business


class ChatCompletionsAuthTests(TestCase):
    def setUp(self):
        Business.objects.create(name="Acme HVAC", slug="acme")
        self.url = reverse("vapi-chat-completions")

    def test_rejects_get(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_accepts_when_no_secret_configured(self):
        # Dev mode: VAPI_WEBHOOK_SECRET unset → endpoint open.
        # Patch the view's reference (imported at module load), not the source
        # module — otherwise the real agent (and a real LLM call) runs.
        with self.settings(VAPI_WEBHOOK_SECRET=""), \
             patch("apps.calls.views.handle_conversation_turn") as mock_turn:
            mock_turn.return_value = {"text": "Hi, this is Mary.", "end_call": False}
            res = self.client.post(
                self.url,
                data='{"messages":[{"role":"user","content":"hello"}]}',
                content_type="application/json",
            )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["choices"][0]["message"]["content"], "Hi, this is Mary.")

    def test_rejects_when_secret_configured_and_missing(self):
        with self.settings(VAPI_WEBHOOK_SECRET="topsecret"):
            res = self.client.post(self.url, data="{}", content_type="application/json")
        self.assertEqual(res.status_code, 401)

    def test_accepts_when_bearer_matches(self):
        with self.settings(VAPI_WEBHOOK_SECRET="topsecret"), \
             patch("apps.calls.views.handle_conversation_turn") as mock_turn:
            mock_turn.return_value = {"text": "ok", "end_call": False}
            res = self.client.post(
                self.url,
                data='{"messages":[{"role":"user","content":"hi"}]}',
                content_type="application/json",
                HTTP_AUTHORIZATION="Bearer topsecret",
            )
        self.assertEqual(res.status_code, 200)


class VapiWebhookTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Acme HVAC", slug="acme")
        self.url = reverse("vapi-webhook")

    def _post_report(self, extract_return=None):
        payload = {
            "message": {
                "type": "end-of-call-report",
                "transcript": "Hi, I need help with my furnace.",
                "summary": "Caller has a furnace issue, lead qualified.",
                "call": {"id": "vapi-call-1", "duration": 42,
                          "customer": {"number": "+15551234567"}},
            },
        }
        extract = extract_return or {
            "customer_name": "Furnace Fred", "customer_email": "", "address": "",
            "project_summary": "Furnace not heating", "trade": "hvac",
            "urgency": "this_week", "temperature": "warm",
            "estimated_value": 300, "follow_up_actions": [],
        }
        with self.settings(VAPI_WEBHOOK_SECRET=""), \
             patch("apps.ai.services.extract_lead_from_transcript", return_value=extract):
            return self.client.post(self.url, data=payload, content_type="application/json")

    def test_end_of_call_report_persists_call(self):
        res = self._post_report()
        self.assertEqual(res.status_code, 200)
        from apps.calls.models import Call
        call = Call.objects.get(provider_call_id="vapi-call-1")
        self.assertEqual(call.status, "completed")
        self.assertEqual(call.from_number, "+15551234567")
        self.assertIn("furnace", call.summary)

    def test_report_recovers_lead_when_agent_captured_nothing(self):
        from apps.leads.models import Lead
        self._post_report()
        lead = Lead.objects.get(extracted_fields__vapi_call_id="vapi-call-1")
        self.assertEqual(lead.extracted_fields.get("source"), "transcript_recovery")
        self.assertEqual(lead.customer.name, "Furnace Fred")
        self.assertEqual(lead.customer.phone, "+15551234567")
        self.assertIn("Furnace", lead.project_summary)

    def test_report_does_not_duplicate_a_lead_the_agent_already_made(self):
        from apps.leads.models import Customer, Lead
        cust = Customer.objects.create(business=self.business, name="Live Caller",
                                       phone="+15551234567")
        Lead.objects.create(business=self.business, customer=cust,
                            project_summary="captured live",
                            extracted_fields={"vapi_call_id": "vapi-call-1"})
        self._post_report()
        self.assertEqual(
            Lead.objects.filter(extracted_fields__vapi_call_id="vapi-call-1").count(), 1)
