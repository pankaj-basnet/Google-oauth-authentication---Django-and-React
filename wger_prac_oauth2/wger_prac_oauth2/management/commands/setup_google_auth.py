from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialApp, SocialAccount

class Command(BaseCommand):
    help = 'Setup Google OAuth and check for logged-in social users'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=str, help='Google Client ID')
        parser.add_argument('--secret', type=str, help='Google Client Secret')
        parser.add_argument('--check', action='store_true', help='List all users logged in via Google')

    def handle(self, *args, **options):
        # --- PHASE 1: CONFIGURATION ---
        if options['id'] and options['secret']:
            # Setup Site
            site = Site.objects.get_or_create(id=1)[0]
            site.domain = 'localhost:8000'
            site.name = 'Localhost'
            site.save()

            # Setup Social App
            app, created = SocialApp.objects.update_or_create(
                provider='google',
                defaults={
                    'name': 'Google Auth',
                    'client_id': options['id'],
                    'secret': options['secret'],
                }
            )
            app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(f'SUCCESS: Google OAuth configured for {site.domain}'))

        # --- PHASE 2: CHECKING LOGGED-IN USERS ---
        if options['check']:
            self.stdout.write(self.style.MIGRATE_LABEL("\n--- Logged-in Google Users ---"))
            google_accounts = SocialAccount.objects.filter(provider='google')
            
            if not google_accounts.exists():
                self.stdout.write(self.style.WARNING("No users have logged in via Google yet."))
            else:
                for acc in google_accounts:
                    user = acc.user
                    self.stdout.write(
                        f"User: {user.username} | Email: {user.email} | Last Login: {user.last_login}"
                    )
            self.stdout.write(self.style.MIGRATE_LABEL("-------------------------------\n"))