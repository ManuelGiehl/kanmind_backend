"""
Management command to create the guest user for frontend guest login.

Must match frontend/shared/js/config.js GUEST_LOGIN (email + password).
Run once: python manage.py create_guest_user
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

# Match frontend config.js GUEST_LOGIN
GUEST_EMAIL = "kevin@kovacsi.de"
GUEST_PASSWORD = "asdasdasd"
GUEST_USERNAME = "guest user"
GUEST_FULLNAME = "Guest User"


class Command(BaseCommand):
    help = "Create guest user for frontend guest login (email/password from config.js)."

    def handle(self, *args, **options):
        User = get_user_model()
        parts = GUEST_FULLNAME.strip().split(maxsplit=1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""
        user = User.objects.filter(email__iexact=GUEST_EMAIL).first()
        if user:
            user.username = GUEST_USERNAME
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(GUEST_PASSWORD)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"Guest user {GUEST_EMAIL} updated.")
            )
            return
        User.objects.create_user(
            username=GUEST_USERNAME,
            email=GUEST_EMAIL,
            password=GUEST_PASSWORD,
            first_name=first_name,
            last_name=last_name,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Guest user {GUEST_EMAIL} created.")
        )
