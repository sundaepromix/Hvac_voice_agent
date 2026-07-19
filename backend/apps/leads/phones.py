"""One canonical phone format so every lookup matches every write.

Numbers reach us in wildly different shapes — Vapi caller ID ("+2349126639036"),
spoken numbers Mary transcribed ("0812 345 6789"), dashboard entries with
punctuation. Storage is normalized E.164-ish (leading + kept, digits only,
"00" international prefix folded into +) and matching falls back to the last
10 digits normalized on both sides, so "+2348147805024" and "08147805024"
resolve to the same customer.
"""
from __future__ import annotations

import re

TAIL_DIGITS = 10
_MIN_TAIL = 7
_PREFILTER_LIMIT = 50


def normalize_phone(raw: str | None) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    plus = s.startswith("+")
    digits = re.sub(r"\D", "", s)
    if not digits:
        return ""
    if not plus and digits.startswith("00") and len(digits) > TAIL_DIGITS:
        digits = digits[2:]
        plus = True
    return ("+" if plus else "") + digits


def phone_tail(raw: str | None, n: int = TAIL_DIGITS) -> str:
    return re.sub(r"\D", "", raw or "")[-n:]


def find_customer_by_phone(business, raw_phone: str | None):
    """The one lookup every caller-matching path goes through.

    Exact normalized match first, then last-10-digit comparison normalized on
    both sides (the endswith on the last 4 is only a cheap DB prefilter).
    """
    from apps.leads.models import Customer

    phone = normalize_phone(raw_phone)
    if not phone or business is None:
        return None
    cust = Customer.objects.filter(business=business, phone=phone).first()
    if cust:
        return cust
    tail = phone_tail(phone)
    if len(tail) < _MIN_TAIL:
        return None
    candidates = (
        Customer.objects.filter(business=business, phone__endswith=tail[-4:])
        .exclude(phone="")[:_PREFILTER_LIMIT]
    )
    for cand in candidates:
        if phone_tail(cand.phone) == tail:
            return cand
    return None
