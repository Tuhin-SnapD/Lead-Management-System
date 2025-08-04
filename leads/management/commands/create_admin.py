"""
Django management command to create an admin account.

Usage:
    python manage.py create_admin
    python manage.py create_admin --username custom_admin --password custom_password
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an admin account with specified or default credentials'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the admin account (default: admin)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin',
            help='Password for the admin account (default: admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Email for the admin account (default: admin@example.com)'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Admin',
            help='First name for the admin account (default: Admin)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='User',
            help='Last name for the admin account (default: User)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if user already exists (will update existing user)'
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        first_name = options['first_name']
        last_name = options['last_name']
        force = options['force']

        try:
            with transaction.atomic():
                # Check if user already exists
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_staff': True,
                        'is_superuser': True,
                        'is_organisor': True,
                        'is_agent': False,
                    }
                )

                if not created and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'User "{username}" already exists. Use --force to update existing user.'
                        )
                    )
                    return

                # Set password and ensure admin privileges
                user.set_password(password)
                user.is_staff = True
                user.is_superuser = True
                user.is_organisor = True
                user.is_agent = False
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.save()

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully created admin account:\n'
                            f'  Username: {username}\n'
                            f'  Email: {email}\n'
                            f'  Password: {password}\n'
                            f'  Full Name: {first_name} {last_name}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully updated admin account:\n'
                            f'  Username: {username}\n'
                            f'  Email: {email}\n'
                            f'  Password: {password}\n'
                            f'  Full Name: {first_name} {last_name}'
                        )
                    )

        except Exception as e:
            raise CommandError(f'Failed to create admin account: {str(e)}') 