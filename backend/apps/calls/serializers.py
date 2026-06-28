from rest_framework import serializers

from .models import Call, OutboundTask


class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = [
            "id", "business", "lead", "provider", "provider_call_id",
            "from_number", "to_number", "status", "duration_seconds",
            "recording_url", "transcript", "summary", "persona_used",
            "started_at", "ended_at",
        ]


class OutboundTaskSerializer(serializers.ModelSerializer):
    contact_name = serializers.SerializerMethodField()
    call_status = serializers.SerializerMethodField()

    class Meta:
        model = OutboundTask
        fields = [
            "id", "kind", "to_number", "contact_name", "objective", "campaign",
            "status", "scheduled_for", "attempts", "max_attempts",
            "last_attempt_at", "last_error", "lead", "call", "call_status",
            "created_at", "updated_at",
        ]

    def get_contact_name(self, obj) -> str:
        cust = getattr(obj.lead, "customer", None) if obj.lead_id else None
        return getattr(cust, "name", "") or ""

    def get_call_status(self, obj) -> str:
        return getattr(obj.call, "status", "") if obj.call_id else ""
