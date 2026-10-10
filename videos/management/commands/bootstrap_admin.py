import os
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = 'Create a missing admin from environment settings; never overwrite existing accounts.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        if not username or not password:
            raise CommandError('Set DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD in hosting settings.')
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write('Existing admin preserved.')
            return
        try:
            validate_password(password, user=User(username=username))
        except ValidationError:
            raise CommandError('Admin password does not meet Django password requirements.') from None
        User.objects.create_superuser(username, os.environ.get('DJANGO_SUPERUSER_EMAIL', ''), password)
        self.stdout.write('Admin created.')
