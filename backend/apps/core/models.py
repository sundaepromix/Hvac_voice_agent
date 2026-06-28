import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from .crypto import EncryptedCharField
from .trades import TRADES


class Business(models.Model):
    """A business using WorkflowAuth (any industry)."""

    TRADE_CHOICES = TRADES

    LLM_PROVIDER_CHOICES = [
        ("anthropic", "Anthropic Claude"),
        ("openai", "OpenAI GPT"),
    ]

    # Prices are quoted in US dollars. The dashboard formats with
    # Intl.NumberFormat; the spoken number guide lives in apps/calls/agent/prompts.py.
    CURRENCY_CHOICES = [
        ("USD", "US Dollar ($)"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    trade = models.CharField(max_length=32, choices=TRADE_CHOICES, default="general")
    timezone = models.CharField(max_length=64, default="UTC")
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default="USD",
        help_text="Prices are quoted in US dollars.",
    )
    phone_number = models.CharField(max_length=32, blank=True, help_text="Public business line")
    voice_persona = models.CharField(
        max_length=64, default="Mary",
        help_text="Display name for the AI agent (configurable per business)"
    )
    knowledge_base = models.TextField(
        blank=True,
        help_text="Pricing rules, FAQ, service area — fed to the LLM as system prompt context",
    )

    llm_provider = models.CharField(
        max_length=16,
        choices=LLM_PROVIDER_CHOICES,
        default="openai",
        help_text="Which LLM powers the Voice Assist and lead extraction.",
    )

    # Provider credentials. When set, override the global env-var defaults.
    # Encrypted at rest via Fernet (apps.core.crypto.EncryptedCharField).
    anthropic_api_key = EncryptedCharField(blank=True, default="")
    openai_api_key = EncryptedCharField(blank=True, default="")
    vapi_api_key = EncryptedCharField(blank=True, default="")
    vapi_phone_number_id = EncryptedCharField(blank=True, default="")
    vapi_assistant_id = models.CharField(
        max_length=128, blank=True, default="",
        help_text="Vapi assistant ID — when set, name + voice persona changes auto-sync to Vapi.",
    )
    twilio_account_sid = EncryptedCharField(blank=True, default="")
    twilio_auth_token = EncryptedCharField(blank=True, default="")
    twilio_from_number = models.CharField(max_length=32, blank=True, default="")  # not a secret

    # WhatsApp Business Cloud API (Meta) — for inbound support tickets.
    whatsapp_access_token = EncryptedCharField(blank=True, default="")
    whatsapp_phone_number_id = models.CharField(max_length=64, blank=True, default="")
    whatsapp_verify_token = EncryptedCharField(blank=True, default="")

    # ---- Outbound calling config (speed-to-lead, follow-ups, reactivation, reminders) ----
    outbound_enabled = models.BooleanField(
        default=True, help_text="Master switch for all outbound calling."
    )
    speed_to_lead_enabled = models.BooleanField(
        default=True, help_text="Auto-call brand-new non-voice leads within a minute of arrival."
    )
    followup_delay_hours = models.PositiveSmallIntegerField(
        default=24, help_text="Hours after a quote is drafted to place a follow-up call."
    )
    reactivation_days = models.PositiveSmallIntegerField(
        default=30, help_text="A lead becomes eligible for reactivation once it's been cold this many days."
    )
    quiet_hours_start = models.PositiveSmallIntegerField(
        default=21, help_text="No outbound calls at or after this hour (0-23, business timezone)."
    )
    quiet_hours_end = models.PositiveSmallIntegerField(
        default=8, help_text="No outbound calls before this hour (0-23, business timezone)."
    )
    do_not_call = models.TextField(
        blank=True, default="", help_text="Phone numbers to never call, one per line."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Businesses"

    def __str__(self) -> str:
        return self.name

    # ---- Resolved credentials (per-business override → global env fallback) ----

    def _resolved(self, attr: str, env_attr: str) -> str:
        from django.conf import settings as dj_settings
        return (getattr(self, attr) or "").strip() or getattr(dj_settings, env_attr, "") or ""

    @property
    def resolved_anthropic_key(self) -> str:
        return self._resolved("anthropic_api_key", "ANTHROPIC_API_KEY")

    @property
    def resolved_openai_key(self) -> str:
        return self._resolved("openai_api_key", "OPENAI_API_KEY")

    @property
    def resolved_vapi_key(self) -> str:
        return self._resolved("vapi_api_key", "VAPI_API_KEY")

    @property
    def resolved_twilio_sid(self) -> str:
        return self._resolved("twilio_account_sid", "TWILIO_ACCOUNT_SID")

    @property
    def resolved_twilio_token(self) -> str:
        return self._resolved("twilio_auth_token", "TWILIO_AUTH_TOKEN")

    @property
    def resolved_twilio_from(self) -> str:
        return self._resolved("twilio_from_number", "TWILIO_FROM_NUMBER")

    @property
    def resolved_whatsapp_token(self) -> str:
        return self._resolved("whatsapp_access_token", "WHATSAPP_ACCESS_TOKEN")

    @property
    def resolved_whatsapp_phone_id(self) -> str:
        return self._resolved("whatsapp_phone_number_id", "WHATSAPP_PHONE_NUMBER_ID")

    @property
    def resolved_whatsapp_verify_token(self) -> str:
        return self._resolved("whatsapp_verify_token", "WHATSAPP_VERIFY_TOKEN")


class LoginCode(models.Model):
    """A short-lived email OTP used as the second factor of login.

    Flow: LoginView verifies password, creates a LoginCode, emails the 6-digit
    code to the user. LoginVerifyView consumes the code (one-shot) and creates
    the session. Codes expire in 10 minutes and tolerate at most 5 wrong
    guesses before being burned.
    """

    CODE_TTL_MINUTES = 10
    MAX_ATTEMPTS = 5

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="login_codes",
    )
    code = models.CharField(max_length=8)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self) -> str:
        return f"LoginCode<{self.user_id}, {self.code[:1]}***>"

    @classmethod
    def issue(cls, user, ip: str = "") -> "LoginCode":
        return cls.objects.create(
            user=user,
            code=f"{secrets.randbelow(1_000_000):06d}",
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(minutes=cls.CODE_TTL_MINUTES),
            ip=ip or None,
        )

    @property
    def is_valid(self) -> bool:
        return (
            self.used_at is None
            and self.attempts < self.MAX_ATTEMPTS
            and timezone.now() < self.expires_at
        )


class Channel(models.Model):
    """One inbound channel a business listens on (phone / sms / whatsapp / email / chat)."""

    KIND_CHOICES = [
        ("phone", "Phone"),
        ("sms", "SMS"),
        ("whatsapp", "WhatsApp"),
        ("email", "Email"),
        ("chat", "Web Chat"),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="channels")
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    address = models.CharField(max_length=255, help_text="phone number, email, etc.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("business", "kind", "address")]

    def __str__(self) -> str:
        return f"{self.business.name} · {self.kind}: {self.address}"
