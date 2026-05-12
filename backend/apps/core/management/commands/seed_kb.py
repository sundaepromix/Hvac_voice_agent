"""One-shot management command to seed the realistic Workflow Auth knowledge base
into the first Business. Idempotent — running it overwrites the KB only.

Usage: docker compose exec backend python manage.py seed_kb
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.core.models import Business


KB = """Workflow Auth is a small, friendly home-services contractor covering HVAC, plumbing, electrical, roofing, and general handyman work in the North Carolina coastal region (252 area code).

# Who we are
- Local team based in Greenville, NC.
- 10 years in business, fully licensed and insured.
- All technicians background-checked. We send the technician name + photo by SMS before arrival.

# Service hours
- Monday to Friday: 8 AM to 6 PM
- Saturday: 9 AM to 3 PM
- Sunday: emergencies only

# Service area
Pitt, Beaufort, Craven, Carteret, Wayne, Lenoir, Greene, and Onslow counties in North Carolina. Outside this area we politely decline and offer to refer to a partner.

# Payment + warranty
- Accept all major cards, ACH, Apple Pay, Cash App, and check.
- Diagnostic fee waived if customer approves the repair the same day.
- 90-day labor warranty on all repairs. Manufacturer warranty on parts (1 to 10 years depending on part).
- 50% deposit on installs over $2,000. Balance due on completion.

# Pricing — STARTING figures and ranges. ALWAYS HEDGE WHEN SPEAKING.

## HVAC
- Diagnostic / service call: $129 (waived if repair approved same day)
- Capacitor replacement: $180 to $280
- Refrigerant top-up (R-410A): $280 to $480
- Thermostat replacement (programmable): $220 to $340
- AC repair, typical: $200 to $800 depending on parts
- Annual tune-up: $149
- AC installation ranges:
  * Window unit: $350 to $650 supply and install
  * Mini-split single zone: $2,800 to $4,200
  * Central AC, 2 to 3 ton: $4,500 to $6,500
- Furnace install: $5,000 to $8,000
- After-hours / emergency surcharge: +$200

## Plumbing
- Service call: $99
- Faucet replacement: $180 + parts
- Toilet repair (flapper / fill valve): $140 to $220
- Toilet replacement: $350 to $650 supply and install
- Drain clear (kitchen / bathroom): $180 to $320
- Main drain clear (with camera): $350 to $550
- Water heater install: $1,800 to $3,500 depending on size and gas vs electric
- Leak repair: $180 to $600

## Electrical
- Service call: $129
- Outlet / switch replacement: $140 plus parts
- Light fixture install: $160 to $280 per fixture
- Ceiling fan install: $220 to $380
- Panel upgrade (200A): $2,500 to $4,000

## Roofing
- Inspection: free in service area
- Small leak / patch repair: $150 to $350
- Shingle replacement (small section): $300 to $700
- Full roof replacement quote: requires on-site survey

## Handyman / general
- Hourly rate: $85/hr, 1-hour minimum
- Small repairs (door, trim, drywall hole, fixture): often $120 to $250 total

# How to speak prices on the phone (CRITICAL)
- ALWAYS use a range OR an "around $X" hedge.
- ALWAYS mention the technician makes the final call on-site.
- Example: "For a small roof patch like that, you're looking at around one fifty to three hundred fifty dollars. Our technician will check the severity once they're on-site and give you the final number — could be a little less or a little more, but we round to a clean figure and document it for you either way."
- Example: "A faucet swap is usually about one eighty plus parts. Once the tech sees what you have we'll confirm the exact figure before doing the work."
- Never quote a single hard number for repair work. Installation pricing can be quoted as the range above.

# FAQs Mary can answer directly
- "Are you licensed?" Yes — fully licensed and insured in North Carolina.
- "Do you offer financing?" Yes, on installs over $2,000. Pre-qualify in 60 seconds via our SMS link after the call.
- "How soon can you come out?" Most repair calls same-day or next-day. Emergencies (no heat / no AC / leak) get a 2-4 hour window.
- "Do you guarantee your work?" 90-day labor warranty on all repairs, plus the manufacturer warranty on any parts we install.
- "What if I just want a quote and not the work?" Free over the phone for installs (rough range). On-site survey may be charged $49 which is credited back if you book the job.
- "Will I be charged if I cancel?" No fee if you cancel by SMS more than 2 hours before the slot.

# Booking rules for Mary
- For REPAIRS where the caller describes the problem: quote the diagnostic fee, offer a specific slot (today or tomorrow), book with book_appointment, send_sms only if they ask.
- For INSTALLATIONS: quote the range from above, offer two specific in-home survey slots, book one. The survey IS the appointment — never say "someone will call you back."
- For QUESTIONS / FAQs: answer from this document. After answering, ask politely: "Anything else I can help with, or would you like to book a visit?" Do NOT push them to book.
- For things this document does not cover: say "Great question, let me have someone from our team call you back with that." Then qualify_lead with what you have. End politely.
- Always run qualify_lead at the start once you have name + reason for call.
"""


class Command(BaseCommand):
    help = "Seed the realistic Workflow Auth KB into the first Business."

    def handle(self, *args, **options):
        b = Business.objects.first()
        if b is None:
            self.stdout.write(self.style.ERROR("No Business found. Run seed_demo first."))
            return
        b.knowledge_base = KB
        b.save(update_fields=["knowledge_base"])
        self.stdout.write(self.style.SUCCESS(
            f"Updated KB for {b.name}: {len(KB)} chars."
        ))
