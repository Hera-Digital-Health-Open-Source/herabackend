from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import IntegrityError
from surveys.models import Survey, SurveySchedule
from surveys.utils import generate_surveys_for_user


class Command(BaseCommand):
    help = 'Generate surveys for all users based on user calendar'

    def add_arguments(self, parser):
        parser.add_argument('--force-create-surveys', dest='force_create_surveys', action='store_true')
        parser.set_defaults(force_create_surveys=False)

    def handle(self, *args, **options):
        force_create_surveys = options['force_create_surveys']
        schedules = SurveySchedule.objects.order_by('calendar_event_type', 'offset_days', 'time_of_day').all()
        users = User.objects.filter(is_active=True).all()
        for user in users:
            self.stdout.write(self.style.SUCCESS(
                f"Generating surveys for user {user.id}"
            ))
            surveys = generate_surveys_for_user(user, schedules, force_create_surveys=force_create_surveys)
            for survey in surveys:
                try:
                    survey.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"Created survey {survey.id} for user {user.id}"
                    ))
                except IntegrityError:
                    pass
        self.stdout.write(self.style.SUCCESS(
            'Finished generating surveys for all users'
        ))
