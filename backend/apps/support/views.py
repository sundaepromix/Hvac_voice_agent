import logging

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Business

from .models import Ticket, TicketMessage
from .serializers import TicketDetailSerializer, TicketListSerializer
from .services.intake import handle_inbound
from .services.whatsapp import parse_webhook, send_text as send_whatsapp_text

logger = logging.getLogger(__name__)


class WhatsAppWebhookView(APIView):
    """Meta WhatsApp Cloud API webhook.

    GET  — verification handshake (echoes hub.challenge when verify_token matches).
    POST — receives a message, runs the support intake pipeline.

    Verification matches against any Business.whatsapp_verify_token; with the
    ENV fallback for single-tenant dev (WHATSAPP_VERIFY_TOKEN).
    """
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        if mode != "subscribe" or not token or not challenge:
            return Response({"detail": "missing_verification_params"}, status=400)

        from django.conf import settings as dj_settings

        env_token = (getattr(dj_settings, "WHATSAPP_VERIFY_TOKEN", "") or "").strip()
        if env_token and token == env_token:
            return Response(int(challenge), status=200)

        for biz in Business.objects.all():
            if biz.resolved_whatsapp_verify_token == token:
                return Response(int(challenge), status=200)

        logger.warning("WhatsApp webhook verification failed.")
        return Response({"detail": "verification_failed"}, status=403)

    def post(self, request):
        inbound = parse_webhook(request.data)
        if inbound is None:
            return Response(status=status.HTTP_200_OK)

        try:
            handle_inbound(
                business=inbound.business,
                channel="whatsapp",
                sender_id=inbound.sender_id,
                sender_name=inbound.sender_name,
                body=inbound.body,
                provider_message_id=inbound.provider_message_id,
            )
        except Exception as exc:  # noqa: BLE001 — Meta retries on non-200; always ack
            logger.exception("[SUPPORT WHATSAPP WEBHOOK] %s", exc)

        return Response(status=status.HTTP_200_OK)


class TicketListView(generics.ListAPIView):
    serializer_class = TicketListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Ticket.objects.all()
        biz_id = self.request.query_params.get("business")
        if biz_id:
            qs = qs.filter(business_id=biz_id)
        status_q = self.request.query_params.get("status")
        if status_q:
            qs = qs.filter(status=status_q)
        channel = self.request.query_params.get("channel")
        if channel:
            qs = qs.filter(channel=channel)
        return qs


class TicketDetailView(generics.RetrieveUpdateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketDetailSerializer
    permission_classes = [IsAuthenticated]


class TicketReplyView(APIView):
    """POST a human-agent reply to a ticket and send it on the original channel."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        ticket = Ticket.objects.filter(pk=pk).first()
        if ticket is None:
            return Response({"detail": "ticket_not_found"}, status=404)

        body = (request.data.get("body") or "").strip()
        if not body:
            return Response({"detail": "body_required"}, status=400)

        send_meta: dict = {"ok": False, "error": "no_sender_for_channel"}
        if ticket.channel == "whatsapp":
            send_meta = send_whatsapp_text(ticket.business, ticket.sender_id, body)

        msg = TicketMessage.objects.create(
            ticket=ticket,
            direction="out",
            author="agent",
            body=body,
            provider_message_id=send_meta.get("provider_message_id", ""),
            metadata={"send_ok": send_meta.get("ok", False), "error": send_meta.get("error", "")},
        )
        ticket.last_message_at = timezone.now()
        if ticket.status == "resolved":
            ticket.status = "open"
        ticket.save(update_fields=["last_message_at", "status", "updated_at"])

        return Response({
            "ok": send_meta.get("ok", False),
            "message_id": msg.pk,
            "error": send_meta.get("error", ""),
        })


class TicketStatusView(APIView):
    """PATCH /tickets/<id>/status/  body: {status, human_only?} — quick agent actions."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk: int):
        ticket = Ticket.objects.filter(pk=pk).first()
        if ticket is None:
            return Response({"detail": "ticket_not_found"}, status=404)

        new_status = request.data.get("status")
        if new_status:
            valid = {choice for choice, _ in Ticket.STATUS_CHOICES}
            if new_status not in valid:
                return Response({"detail": f"status must be one of {sorted(valid)}"}, status=400)
            ticket.status = new_status

        if "human_only" in request.data:
            ticket.human_only = bool(request.data.get("human_only"))

        ticket.save()
        return Response({"id": ticket.pk, "status": ticket.status, "human_only": ticket.human_only})


class ContactTicketView(APIView):
    """POST /api/support/tickets/contact/  — public contact-form submission.

    Body: {name, email, subject, body}
    Stores a Ticket in the DB and emails TICKET_NOTIFY_EMAIL so we see it instantly.
    """
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        import os
        from django.core.mail import EmailMessage
        from django.conf import settings as dj_settings

        name = (request.data.get("name") or "").strip()
        email = (request.data.get("email") or "").strip()
        subject = (request.data.get("subject") or "").strip() or "(no subject)"
        body = (request.data.get("body") or "").strip()

        if not email or not body:
            return Response({"detail": "email_and_body_required"}, status=400)

        biz = Business.objects.first()
        if biz is None:
            return Response({"detail": "no_business_configured"}, status=500)

        ticket = (
            Ticket.objects.filter(business=biz, channel="email", sender_id=email)
            .exclude(status="resolved")
            .order_by("-created_at")
            .first()
        )
        if ticket is None:
            ticket = Ticket.objects.create(
                business=biz,
                channel="email",
                sender_id=email,
                sender_name=name or email,
                subject=subject[:255],
            )
        elif name and not ticket.sender_name:
            ticket.sender_name = name
        TicketMessage.objects.create(
            ticket=ticket,
            direction="in",
            author="customer",
            body=body,
        )
        ticket.last_message_at = timezone.now()
        ticket.save(update_fields=["sender_name", "last_message_at", "updated_at"])

        notify_to = os.environ.get("TICKET_NOTIFY_EMAIL", "").strip()
        if notify_to and getattr(dj_settings, "EMAIL_HOST", ""):
            try:
                from_addr = getattr(dj_settings, "DEFAULT_FROM_EMAIL", "no-reply@workflowauth.com")
                mail_body = (
                    f"New ticket #{ticket.pk} from the contact form.\n\n"
                    f"Name:    {name or '(unknown)'}\n"
                    f"Email:   {email}\n"
                    f"Subject: {subject}\n\n"
                    f"---\n{body}\n---\n\n"
                    f"View / reply in the dashboard."
                )
                EmailMessage(
                    subject=f"[Workflow Auth ticket #{ticket.pk}] {subject}",
                    body=mail_body,
                    from_email=from_addr,
                    to=[notify_to],
                    reply_to=[email] if email else None,
                ).send(fail_silently=False)
                logger.info("[CONTACT TICKET] ticket=%s emailed to %s", ticket.pk, notify_to)
            except Exception as exc:  # noqa: BLE001 — SMTP errors are noisy; never block ticket creation
                logger.error("[CONTACT TICKET EMAIL ERROR] ticket=%s err=%s", ticket.pk, exc)
        else:
            logger.info("[CONTACT TICKET] ticket=%s — no notify email configured (set TICKET_NOTIFY_EMAIL + EMAIL_HOST)", ticket.pk)

        return Response({"conversation_id": str(ticket.pk), "ticket_id": ticket.pk})
