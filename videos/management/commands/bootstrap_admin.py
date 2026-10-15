import os
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = 'Create a missing admin; reset an existing password only during an explicitly configured recovery window.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        if not username or not password:
            raise CommandError('Set DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD in hosting settings.')
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            import time
            try:
                recovery_until = int(os.environ.get('DJANGO_ADMIN_RECOVERY_UNTIL', '0'))
            except ValueError:
                raise CommandError('Invalid admin recovery expiry.') from None
            if time.time() < recovery_until <= time.time() + 1800:
                user = User.objects.get(username=username)
                if not user.is_superuser or not user.is_active:
                    raise CommandError('Recovery requires an existing active superuser.')
                try:
                    validate_password(password, user=user)
                except ValidationError:
                    raise CommandError('Admin password does not meet Django password requirements.') from None
                if not user.check_password(password):
                    user.set_password(password)
                    user.save(update_fields=['password'])
                self.stdout.write('Admin password recovery completed.')
                return
            self.stdout.write('Existing admin preserved.')
            return
        try:
            validate_password(password, user=User(username=username))
        except ValidationError:
            raise CommandError('Admin password does not meet Django password requirements.') from None
        User.objects.create_superuser(username, os.environ.get('DJANGO_SUPERUSER_EMAIL', ''), password)
        self.stdout.write('Admin created.')
