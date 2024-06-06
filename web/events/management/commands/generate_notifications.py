from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from events.models import NotificationSchedule
from events.utils import generate_notification_events_for_user
import datetime

class Command(BaseCommand):
    help = 'Generate notifications for all users based on user calendar'

    def add_arguments(self, parser):
        parser.add_argument('--force-create-events', dest='force_create_events', action='store_true')
        parser.set_defaults(force_create_events=False)

    def handle(self, *args, **options):
        force_create_events = options['force_create_events']
        schedules = NotificationSchedule.objects.order_by('calendar_event_type', 'offset_days', 'time_of_day').all()
        self.stdout.write(self.style.SUCCESS(
            f"Loaded {len(schedules)} NotificationSchedules"
        ))
        users = User.objects.filter(is_active=True).all()
        for user in users:
            self.stdout.write(self.style.SUCCESS(
                f"Generating notifications for user {user.id}"
            ))
            notification_events = generate_notification_events_for_user(user, schedules,
                                                                        force_create_events=force_create_events)
            for event in notification_events:
                try:
                    event.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"Created NotificationEvent {event.id} for user {user.id}"
                    ))
                except IntegrityError:
                    pass
        self.stdout.write(self.style.SUCCESS(
            'Finished generating notifications for all users'
        ))
