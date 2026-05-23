from rest_framework import serializers

from .models import Ticket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = ["id", "direction", "author", "body", "created_at", "metadata"]
        read_only_fields = fields


class TicketListSerializer(serializers.ModelSerializer):
    last_message_preview = serializers.SerializerMethodField()
    message_count = serializers.IntegerField(source="messages.count", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "channel", "sender_id", "sender_name", "subject", "status",
            "human_only", "last_message_at", "created_at", "last_message_preview",
            "message_count",
        ]
        read_only_fields = fields

    def get_last_message_preview(self, obj: Ticket) -> str:
        msg = obj.messages.order_by("-created_at").first()
        return msg.body[:140] if msg else ""


class TicketDetailSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "channel", "sender_id", "sender_name", "subject", "status",
            "human_only", "last_message_at", "created_at", "messages",
        ]
        read_only_fields = ["id", "channel", "sender_id", "last_message_at", "created_at", "messages"]
