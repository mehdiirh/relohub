from django.core.management.base import BaseCommand, no_translations

from user.models import User


class Command(BaseCommand):
    @no_translations
    def handle(self, *args, **options):
        if not User.objects.filter(username="admin"):
            self.stdout.write("Creating superuser...")
            User.objects.create_superuser(username="admin", password="(#ChangeMe!)")
            self.stdout.write("Superuser created")
            return

        self.stderr.write("Superuser already exists")
