"""Scheduling service — Google Calendar when configured, stub slots otherwise.

Set GOOGLE_CALENDAR_CREDENTIALS_PATH (service-account JSON key) and
GOOGLE_CALENDAR_ID in .env, and share the calendar with the service account's
client_email. Without them every call falls back to the deterministic stub so
dev and demos keep working.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import time as _time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Default service hours: 8 AM – 6 PM weekdays, 9 AM – 2 PM Saturdays, closed Sundays
DEFAULT_DAILY_SLOTS_WEEKDAY = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]
DEFAULT_DAILY_SLOTS_SATURDAY = ["09:00", "10:00", "11:00", "12:00", "13:00"]

_GCAL_SCOPE = "https://www.googleapis.com/auth/calendar"
_GCAL_TOKEN_CACHE_KEY = "gcal_access_token"
# Keep network budgets tight — this runs inside a live voice turn.
_HTTP_TIMEOUT = 5


def _load_service_account() -> dict | None:
    path = (getattr(settings, "GOOGLE_CALENDAR_CREDENTIALS_PATH", "") or "").strip()
    cal_id = (getattr(settings, "GOOGLE_CALENDAR_ID", "") or "").strip()
    if not path or not cal_id or not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            info = json.load(fh)
        if info.get("client_email") and info.get("private_key"):
            return info
    except (OSError, ValueError) as exc:
        logger.warning("[GCAL] unreadable credentials file %s: %s", path, exc)
    return None


def _b64url(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def _access_token() -> str | None:
    """Service-account OAuth token via a signed JWT (RS256, `cryptography`)."""
    cached = cache.get(_GCAL_TOKEN_CACHE_KEY)
    if cached:
        return cached
    info = _load_service_account()
    if not info:
        return None
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        now = int(_time.time())
        header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
        token_uri = info.get("token_uri") or "https://oauth2.googleapis.com/token"
        claims = _b64url(json.dumps({
            "iss": info["client_email"],
            "scope": _GCAL_SCOPE,
            "aud": token_uri,
            "iat": now,
            "exp": now + 3600,
        }).encode())
        signing_input = header + b"." + claims
        key = serialization.load_pem_private_key(info["private_key"].encode(), password=None)
        signature = _b64url(key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256()))
        assertion = (signing_input + b"." + signature).decode()

        resp = requests.post(token_uri, data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }, timeout=_HTTP_TIMEOUT)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if token:
            cache.set(_GCAL_TOKEN_CACHE_KEY, token, timeout=50 * 60)
        return token
    except Exception as exc:  # noqa: BLE001 — calendar must never break a live call
        logger.warning("[GCAL] token exchange failed: %s", exc)
        return None


def _busy_ranges(date: datetime.date, tz: ZoneInfo, token: str) -> list[tuple[datetime, datetime]] | None:
    """Busy intervals for the calendar on `date`, or None when the query fails."""
    cal_id = settings.GOOGLE_CALENDAR_ID
    day_start = datetime.combine(date, datetime.min.time(), tzinfo=tz)
    day_end = day_start + timedelta(days=1)
    try:
        resp = requests.post(
            "https://www.googleapis.com/calendar/v3/freeBusy",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "timeMin": day_start.isoformat(),
                "timeMax": day_end.isoformat(),
                "items": [{"id": cal_id}],
            },
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        busy = resp.json().get("calendars", {}).get(cal_id, {}).get("busy", [])
        out: list[tuple[datetime, datetime]] = []
        for b in busy:
            start = datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
            out.append((start, end))
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning("[GCAL] freeBusy failed: %s", exc)
        return None


def _stub_available(date_str: str, date: datetime.date, slots: list[str]) -> list[str]:
    # Stub: drop a deterministic subset by date hash so it feels realistic
    h = sum(map(ord, date_str)) % 4
    booked_idx = {h, (h + 3) % len(slots)}
    return [s for i, s in enumerate(slots) if i not in booked_idx]


def check_availability(date_str: str, trade: str | None = None,
                       tz_name: str = "America/Los_Angeles") -> dict:
    """Return available start times for a given date.

    Uses Google Calendar free/busy when a service account is configured;
    otherwise (or on any calendar error) falls back to the stub so a live
    call never dead-ends.
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"available": [], "error": f"Invalid date format: {date_str}. Use YYYY-MM-DD."}

    try:
        tz = ZoneInfo(tz_name)
    except Exception:  # noqa: BLE001
        tz = ZoneInfo("America/Los_Angeles")

    # Closed Sunday
    if date.weekday() == 6:
        return {"date": date_str, "available": [], "note": "Closed Sundays."}

    now = datetime.now(tz)
    if date < now.date():
        return {"date": date_str, "available": [], "note": "That date is in the past."}

    slots = list(DEFAULT_DAILY_SLOTS_SATURDAY) if date.weekday() == 5 else list(DEFAULT_DAILY_SLOTS_WEEKDAY)

    # Never offer a start time that's already passed (or is within the hour).
    if date == now.date():
        cutoff = (now + timedelta(hours=1)).strftime("%H:%M")
        slots = [s for s in slots if s >= cutoff]
        if not slots:
            return {"date": date_str, "available": [],
                    "note": "No slots left today — offer the next business day."}

    token = _access_token()
    if token:
        busy = _busy_ranges(date, tz, token)
        if busy is not None:
            available: list[str] = []
            for s in slots:
                start = datetime.combine(date, datetime.strptime(s, "%H:%M").time(), tzinfo=tz)
                end = start + timedelta(minutes=60)
                if not any(b_start < end and start < b_end for b_start, b_end in busy):
                    available.append(s)
            return {"date": date_str, "available": available, "trade": trade, "source": "google_calendar"}

    return {"date": date_str, "available": _stub_available(date_str, date, slots), "trade": trade}


def create_calendar_event(*, date_str: str, time_str: str, duration_minutes: int = 60,
                          summary: str = "", description: str = "",
                          tz_name: str = "America/Los_Angeles") -> str | None:
    """Best-effort: insert the booked appointment into Google Calendar.

    Returns the event id, or None when the calendar isn't configured or the
    insert fails — booking in the dashboard succeeds either way.
    """
    token = _access_token()
    if not token:
        return None
    when = parse_when(date_str, time_str)
    if not when:
        return None
    try:
        tz = ZoneInfo(tz_name)
    except Exception:  # noqa: BLE001
        tz = ZoneInfo("America/Los_Angeles")
    start = when.replace(tzinfo=tz)
    end = start + timedelta(minutes=duration_minutes or 60)
    try:
        resp = requests.post(
            f"https://www.googleapis.com/calendar/v3/calendars/{settings.GOOGLE_CALENDAR_ID}/events",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "summary": summary or "Service appointment",
                "description": description,
                "start": {"dateTime": start.isoformat(), "timeZone": tz_name},
                "end": {"dateTime": end.isoformat(), "timeZone": tz_name},
            },
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        event_id = resp.json().get("id")
        logger.info("[GCAL] event created %s (%s %s)", event_id, date_str, time_str)
        return event_id
    except Exception as exc:  # noqa: BLE001
        logger.warning("[GCAL] event insert failed: %s", exc)
        return None


def parse_when(date_str: str, time_str: str) -> datetime | None:
    """Parse a (date, time) pair into a datetime. Used for booking validation."""
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
        except ValueError:
            return None


def humanize_when(when: datetime) -> str:
    return when.strftime("%A %B %d at %I:%M %p")


def end_of_window(when: datetime, duration_minutes: int = 60) -> datetime:
    return when + timedelta(minutes=duration_minutes)
