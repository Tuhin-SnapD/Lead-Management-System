"""
Django management command to generate sample agents.

Usage:
    python manage.py generate_agents
    python manage.py generate_agents --count 5
    python manage.py generate_agents --count 10 --organisation admin
"""

import random
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from leads.models import Agent, UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate sample agents with realistic data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of agents to generate (default: 3)'
        )
        parser.add_argument(
            '--organisation',
            type=str,
            default='admin',
            help='Username of the organisation owner (default: admin)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing agents before generating new ones'
        )

    def handle(self, *args, **options):
        count = options['count']
        org_username = options['organisation']
        clear_existing = options['clear']

        try:
            # Get the organisation
            try:
                org_user = User.objects.get(username=org_username)
                organisation = org_user.userprofile
            except User.DoesNotExist:
                raise CommandError(f'User "{org_username}" does not exist')

            # Sample data for generating realistic agents
            first_names = [
                'Alex', 'Jordan', 'Casey', 'Taylor', 'Morgan', 'Riley', 'Quinn', 'Avery',
                'Blake', 'Cameron', 'Drew', 'Emery', 'Finley', 'Gray', 'Harper', 'Indigo',
                'Jamie', 'Kendall', 'Logan', 'Mason', 'Noah', 'Oakley', 'Parker', 'Quinn',
                'Rowan', 'Sage', 'Tatum', 'Unity', 'Val', 'Winter', 'Xander', 'Yuki', 'Zion'
            ]

            last_names = [
                'Anderson', 'Brown', 'Clark', 'Davis', 'Evans', 'Fisher', 'Garcia', 'Harris',
                'Jackson', 'Johnson', 'King', 'Lee', 'Miller', 'Nelson', 'Parker', 'Quinn',
                'Roberts', 'Smith', 'Taylor', 'Walker', 'White', 'Young', 'Adams', 'Baker',
                'Campbell', 'Carter', 'Collins', 'Cooper', 'Cox', 'Edwards', 'Green', 'Hall',
                'Hill', 'Hughes', 'James', 'Jones', 'Kelly', 'Lewis', 'Martin', 'Mitchell',
                'Moore', 'Morris', 'Murphy', 'Patterson', 'Phillips', 'Reed', 'Richardson',
                'Roberts', 'Robinson', 'Scott', 'Stewart', 'Thompson', 'Turner', 'Ward',
                'Watson', 'Williams', 'Wilson', 'Wood', 'Wright', 'Young', 'Allen', 'Bailey',
                'Bell', 'Bennett', 'Black', 'Brooks', 'Butler', 'Campbell', 'Carter', 'Clark',
                'Collins', 'Cook', 'Cooper', 'Cox', 'Cruz', 'Davis', 'Edwards', 'Evans',
                'Fisher', 'Flores', 'Foster', 'Garcia', 'Gonzalez', 'Gray', 'Green', 'Hall',
                'Harris', 'Hayes', 'Hill', 'Howard', 'Hughes', 'Jackson', 'James', 'Johnson',
                'Jones', 'Kelly', 'King', 'Lee', 'Lewis', 'Lopez', 'Martin', 'Miller',
                'Mitchell', 'Moore', 'Morgan', 'Morris', 'Murphy', 'Nelson', 'Parker',
                'Patterson', 'Perez', 'Peterson', 'Phillips', 'Powell', 'Price', 'Reed',
                'Richardson', 'Roberts', 'Robinson', 'Rodriguez', 'Rogers', 'Ross', 'Russell',
                'Sanders', 'Scott', 'Smith', 'Stewart', 'Taylor', 'Thomas', 'Thompson',
                'Turner', 'Walker', 'Ward', 'Watson', 'White', 'Williams', 'Wilson', 'Wood',
                'Wright', 'Young', 'Adams', 'Allen', 'Baker', 'Bell', 'Bennett', 'Black',
                'Brooks', 'Butler', 'Campbell', 'Carter', 'Clark', 'Collins', 'Cook',
                'Cooper', 'Cox', 'Cruz', 'Davis', 'Edwards', 'Evans', 'Fisher', 'Flores',
                'Foster', 'Garcia', 'Gonzalez', 'Gray', 'Green', 'Hall', 'Harris', 'Hayes',
                'Hill', 'Howard', 'Hughes', 'Jackson', 'James', 'Johnson', 'Jones', 'Kelly',
                'King', 'Lee', 'Lewis', 'Lopez', 'Martin', 'Miller', 'Mitchell', 'Moore',
                'Morgan', 'Morris', 'Murphy', 'Nelson', 'Parker', 'Patterson', 'Perez',
                'Peterson', 'Phillips', 'Powell', 'Price', 'Reed', 'Richardson', 'Roberts',
                'Robinson', 'Rodriguez', 'Rogers', 'Ross', 'Russell', 'Sanders', 'Scott',
                'Smith', 'Stewart', 'Taylor', 'Thomas', 'Thompson', 'Turner', 'Walker',
                'Ward', 'Watson', 'White', 'Williams', 'Wilson', 'Wood', 'Wright', 'Young'
            ]

            # Clear existing agents if requested
            if clear_existing:
                Agent.objects.filter(organisation=organisation).delete()
                self.stdout.write(
                    self.style.WARNING(f'Cleared existing agents for organisation "{org_username}"')
                )

            # Generate agents
            agents_created = 0
            with transaction.atomic():
                for i in range(count):
                    # Generate random agent data
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
                    email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(['company.com', 'sales.com', 'business.com'])}"
                    
                    # Create user for the agent
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='password123',
                        first_name=first_name,
                        last_name=last_name,
                        is_organisor=False,
                        is_agent=True
                    )
                    
                    # Create the agent
                    agent = Agent.objects.create(
                        user=user,
                        organisation=organisation,
                        is_active=True
                    )
                    
                    agents_created += 1
                    self.stdout.write(f'Created agent: {first_name} {last_name} ({email})')

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {agents_created} agents for organisation "{org_username}"\n'
                    f'All agents have password: password123'
                )
            )

        except Exception as e:
            raise CommandError(f'Failed to generate agents: {str(e)}') 