"""Place any outbound calls whose scheduled time has arrived.

Invoked by Vercel Cron (via the protected /api/calls/outbound/cron/ endpoint) or
manually: `python manage.py run_outbound_queue`.
"""
from django.core.management.base import BaseCommand

from apps.calls.services.outbound import run_due_tasks


class Command(BaseCommand):
    help = "Place outbound calls for any due tasks in the queue."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=25)

    def handle(self, *args, **options):
        summary = run_due_tasks(limit=options["limit"])
        self.stdout.write(self.style.SUCCESS(f"Outbound queue run: {summary}"))
