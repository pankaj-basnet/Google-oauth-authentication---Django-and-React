from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Setup Google SocialApp and Site for OAuth'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=str, required=True, help='Google Client ID')
        parser.add_argument('--secret', type=str, required=True, help='Google Client Secret')

    def handle(self, *args, **options):
        # 1. Setup the Site (Crucial for allauth)
        site = Site.objects.get_or_create(id=1)[0]
        site.domain = 'localhost:8000'
        site.name = 'Localhost'
        site.save()

        # 2. Setup the Social App
        app, created = SocialApp.objects.update_or_create(
            provider='google',
            defaults={
                'name': 'Google Auth',
                'client_id': options['id'],
                'secret': options['secret'],
            }
        )
        app.sites.add(site)

        self.stdout.write(self.style.SUCCESS(f'Successfully configured Google OAuth for {site.domain}'))