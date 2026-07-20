from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from designer import emails
from designer.models import DesignRequest

REMINDER_AFTER = timedelta(days=2)
ESCALATE_AFTER = timedelta(days=3)


class Command(BaseCommand):
    help = (
        'Reminds clients and then notifies admin about DesignRequests still '
        'waiting on a deferred logo upload. Intended to run daily via cron.'
    )

    def handle(self, *args, **options):
        now = timezone.now()

        to_remind = list(DesignRequest.objects.filter(
            status=DesignRequest.Status.LOGO_DEFERRED,
            reminder_sent_at__isnull=True,
            logo_deferred_at__lte=now - REMINDER_AFTER,
        ))
        for design_request in to_remind:
            emails.notify_client_reminder(design_request)
            design_request.reminder_sent_at = now
            design_request.status = DesignRequest.Status.REMINDED
            design_request.save(update_fields=['reminder_sent_at', 'status'])
            self.stdout.write(f'Reminded client for order {design_request.order_number}')

        to_escalate = list(DesignRequest.objects.filter(
            status=DesignRequest.Status.REMINDED,
            escalated_at__isnull=True,
            logo_deferred_at__lte=now - ESCALATE_AFTER,
        ))
        for design_request in to_escalate:
            emails.notify_admin_escalation(design_request)
            design_request.escalated_at = now
            design_request.status = DesignRequest.Status.ESCALATED
            design_request.save(update_fields=['escalated_at', 'status'])
            self.stdout.write(f'Escalated order {design_request.order_number} to admin')

        self.stdout.write(self.style.SUCCESS(
            f'Done. Reminded: {len(to_remind)}, escalated: {len(to_escalate)}.'
        ))
