import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0006_business_whatsapp_credentials"),
        ("leads", "0002_lead_leads_lead_busines_4fd20a_idx"),
    ]

    operations = [
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("channel", models.CharField(choices=[("whatsapp", "WhatsApp"), ("sms", "SMS"), ("email", "Email"), ("webchat", "Web Chat")], max_length=16)),
                ("sender_id", models.CharField(help_text="WhatsApp number, email address, or chat-session ID. Identifies the customer on this channel.", max_length=255)),
                ("sender_name", models.CharField(blank=True, default="", max_length=200)),
                ("subject", models.CharField(blank=True, default="", max_length=255)),
                ("status", models.CharField(choices=[("open", "Open"), ("waiting", "Waiting on customer"), ("escalated", "Escalated to human"), ("resolved", "Resolved")], default="open", max_length=16)),
                ("human_only", models.BooleanField(default=False, help_text="If true, AI will not auto-reply — only human agents respond.")),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tickets", to="core.business")),
                ("customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tickets", to="leads.customer")),
            ],
            options={
                "ordering": ["-last_message_at", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("direction", models.CharField(choices=[("in", "Inbound"), ("out", "Outbound")], max_length=4)),
                ("author", models.CharField(choices=[("customer", "Customer"), ("ai", "AI"), ("agent", "Human agent"), ("system", "System")], max_length=16)),
                ("body", models.TextField()),
                ("provider_message_id", models.CharField(blank=True, default="", help_text="WhatsApp/Twilio message id — used to dedup webhook retries.", max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="support.ticket")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(fields=["business", "status", "-last_message_at"], name="support_tic_busines_b00e2d_idx"),
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(fields=["channel", "sender_id", "status"], name="support_tic_channel_4f1a82_idx"),
        ),
        migrations.AddConstraint(
            model_name="ticket",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "resolved"), _negated=True),
                fields=("business", "channel", "sender_id"),
                name="support_ticket_one_open_per_sender",
            ),
        ),
        migrations.AddIndex(
            model_name="ticketmessage",
            index=models.Index(fields=["ticket", "created_at"], name="support_tic_ticket__27e9a3_idx"),
        ),
        migrations.AddIndex(
            model_name="ticketmessage",
            index=models.Index(fields=["provider_message_id"], name="support_tic_provide_3b7c04_idx"),
        ),
    ]
