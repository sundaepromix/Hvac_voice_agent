"""Session-based auth endpoints for the Workflow Auth dashboard.

Two-step login with email OTP:

  POST /api/auth/login/         { username|email, password }
      -> { requires_otp: true, login_token, email_masked }
      -> emails a 6-digit code to the user's address

  POST /api/auth/login/verify/  { login_token, code }
      -> sets sessionid cookie, returns user

  POST /api/auth/logout/                                       -> clears session
  GET  /api/auth/me/                                           -> current user or 401

If a user has no email on file (legacy data), the first step bypasses OTP and
creates the session directly — but logs a warning so admins can backfill.
"""
from __future__ import annotations

import logging

from django.conf import settings as dj_settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.mail import EmailMessage
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.core import is_ratelimited
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LoginCode

logger = logging.getLogger(__name__)


def _serialize(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "is_staff": user.is_staff,
    }


def _mask_email(email: str) -> str:
    """jane@example.com -> j***@example.com (so the UI can show 'check your inbox at j***@example.com')."""
    email = (email or "").strip()
    if "@" not in email:
        return email
    name, domain = email.split("@", 1)
    if len(name) <= 1:
        return f"{name}@{domain}"
    return f"{name[0]}***@{domain}"


def _send_login_code(user, code: str) -> str:
    """Email the OTP.

    Returns a delivery status the caller uses to decide whether the user can
    proceed to the code-entry step:

      "sent"    — handed to SMTP successfully.
      "no_smtp" — no SMTP configured. Code is logged to stdout as a dev fallback.
      "failed"  — SMTP configured but send() raised (bad creds, blocked IP, …).

    A silent failure here used to trap users on the "check your email" screen
    with a code that was never delivered, so callers must treat anything other
    than "sent" as a hard error in production.
    """
    if not user.email:
        return "no_smtp"
    has_smtp = bool(
        getattr(dj_settings, "EMAIL_HOST", "")
        and getattr(dj_settings, "EMAIL_HOST_USER", "")
    )
    if not has_smtp:
        # Dev fallback so you can copy the code from `docker compose logs backend`.
        logger.info("[LOGIN OTP] (no SMTP) user=%s code=%s", user.email, code)
        return "no_smtp"

    from_addr = getattr(dj_settings, "DEFAULT_FROM_EMAIL", "no-reply@workflowauth.com")
    body = (
        f"Hi {user.first_name or user.username},\n\n"
        f"Your Workflow Auth sign-in code is:\n\n"
        f"    {code}\n\n"
        f"This code expires in {LoginCode.CODE_TTL_MINUTES} minutes. If you didn't "
        f"try to sign in, ignore this email — someone may have typed your address by mistake.\n\n"
        f"— Workflow Auth"
    )
    try:
        EmailMessage(
            subject=f"Workflow Auth sign-in code: {code}",
            body=body,
            from_email=from_addr,
            to=[user.email],
        ).send(fail_silently=False)
        logger.info("[LOGIN OTP] sent user=%s", user.email)
        return "sent"
    except Exception as exc:  # noqa: BLE001
        logger.error("[LOGIN OTP] email failed user=%s err=%s", user.email, exc)
        return "failed"


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    """Step 1 of the login flow — validate password, issue + email OTP."""
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        if is_ratelimited(request, group="login-ip", key="ip", rate="10/5m", increment=False):
            return Response(
                {"detail": "Too many login attempts. Try again in a few minutes."},
                status=429,
            )

        identifier = (request.data.get("username") or request.data.get("email") or "").strip()
        password = request.data.get("password") or ""
        if not identifier or not password:
            return Response({"detail": "Username and password are required."}, status=400)

        user_key = identifier.lower()
        if is_ratelimited(
            request, group="login-user", key=lambda _g, _r: user_key,
            rate="10/5m", increment=False,
        ):
            return Response(
                {"detail": "Too many login attempts for this account. Try again later."},
                status=429,
            )

        user = authenticate(request, username=identifier, password=password)
        if user is None and "@" in identifier:
            User = get_user_model()
            try:
                match = User.objects.get(email__iexact=identifier)
                user = authenticate(request, username=match.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is None:
            is_ratelimited(request, group="login-ip", key="ip", rate="10/5m", increment=True)
            is_ratelimited(
                request, group="login-user", key=lambda _g, _r: user_key,
                rate="10/5m", increment=True,
            )
            return Response({"detail": "Invalid credentials."}, status=401)
        if not user.is_active:
            return Response({"detail": "Account is disabled."}, status=403)

        # OTP is opt-in. When LOGIN_REQUIRE_OTP is off (the default), a correct
        # password grants the session directly — no email round-trip, no lockout
        # if SMTP is down. Flip LOGIN_REQUIRE_OTP=1 to re-enable 2-step login.
        if not getattr(dj_settings, "LOGIN_REQUIRE_OTP", False):
            login(request, user)
            return Response({"user": _serialize(user), "requires_otp": False})

        # No email on the user record? Skip OTP and grant session directly
        # (legacy/safety path so users aren't locked out forever). Warn loudly.
        if not user.email:
            logger.warning(
                "[LOGIN OTP] user=%s has no email — granting session without OTP. "
                "Backfill the email to enforce 2-step login.", user.username,
            )
            login(request, user)
            return Response({
                "user": _serialize(user),
                "requires_otp": False,
                "skipped_otp_reason": "no_email_on_account",
            })

        code = LoginCode.issue(
            user=user,
            ip=request.META.get("REMOTE_ADDR", ""),
        )
        status = _send_login_code(user, code.code)

        # Never strand the user on the code screen with a code they can't receive.
        # "failed" (SMTP send raised) is always a hard error. "no_smtp" is only
        # tolerated in DEBUG, where the code is logged to stdout for local dev;
        # in production it means email isn't configured — surface it instead of
        # asking for a code that was never sent.
        if status == "failed" or (status == "no_smtp" and not dj_settings.DEBUG):
            return Response(
                {"detail": "We couldn't send your sign-in code. Please try again "
                           "in a moment, or contact support if this keeps happening."},
                status=503,
            )

        return Response({
            "requires_otp": True,
            "login_token": code.token,
            "email_masked": _mask_email(user.email),
            "expires_in_minutes": LoginCode.CODE_TTL_MINUTES,
            # In dev where SMTP isn't configured the code is logged but not emailed.
            # We never echo the code back in the API response — admins read it from logs.
            "delivered": status == "sent",
        })


@method_decorator(csrf_exempt, name="dispatch")
class LoginVerifyView(APIView):
    """Step 2 — exchange a code for a session."""
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        if is_ratelimited(request, group="login-verify-ip", key="ip", rate="20/5m", increment=True):
            return Response(
                {"detail": "Too many verification attempts. Try again in a few minutes."},
                status=429,
            )

        token = (request.data.get("login_token") or "").strip()
        code = (request.data.get("code") or "").strip()
        if not token or not code:
            return Response({"detail": "login_token and code are required."}, status=400)

        login_code = LoginCode.objects.filter(token=token).select_related("user").first()
        if login_code is None:
            return Response({"detail": "Invalid or expired code."}, status=401)
        if not login_code.is_valid:
            return Response({"detail": "Code has expired. Please sign in again."}, status=401)

        # Compare safely; bump attempts on mismatch so brute force is limited.
        if code != login_code.code:
            login_code.attempts = (login_code.attempts or 0) + 1
            login_code.save(update_fields=["attempts"])
            remaining = LoginCode.MAX_ATTEMPTS - login_code.attempts
            if remaining <= 0:
                return Response({"detail": "Too many wrong codes. Please sign in again."}, status=401)
            return Response(
                {"detail": f"Wrong code. {remaining} attempt(s) left."},
                status=401,
            )

        from django.utils import timezone
        login_code.used_at = timezone.now()
        login_code.save(update_fields=["used_at"])

        user = login_code.user
        if not user.is_active:
            return Response({"detail": "Account is disabled."}, status=403)

        login(request, user)
        return Response({"user": _serialize(user)})


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        logout(request)
        return Response({"ok": True})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": _serialize(request.user)})
