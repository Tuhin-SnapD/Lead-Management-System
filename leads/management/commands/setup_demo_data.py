"""
Management command to set up demo data for the Lead Management System.

This command creates sample users, agents, categories, and leads for testing
and demonstration purposes.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from leads.models import Lead, Agent, Category
from leads.services import CategoryService

User = get_user_model()


class Command(BaseCommand):
    """Management command to set up demo data."""
    
    help = 'Set up demo data for the Lead Management System'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating demo data',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Lead.objects.all().delete()
            Agent.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        self.stdout.write('Setting up demo data...')
        
        # Create organizer user
        organizer = User.objects.create_user(
            username='demo_organizer',
            email='organizer@demo.com',
            password='demo123',
            first_name='Demo',
            last_name='Organizer',
            is_organisor=True,
            is_agent=False
        )
        self.stdout.write(f'Created organizer: {organizer.email}')

        # Create agent users
        agents_data = [
            {
                'username': 'agent1',
                'email': 'agent1@demo.com',
                'first_name': 'John',
                'last_name': 'Smith'
            },
            {
                'username': 'agent2',
                'email': 'agent2@demo.com',
                'first_name': 'Jane',
                'last_name': 'Doe'
            },
            {
                'username': 'agent3',
                'email': 'agent3@demo.com',
                'first_name': 'Mike',
                'last_name': 'Johnson'
            }
        ]

        agents = []
        for agent_data in agents_data:
            user = User.objects.create_user(
                username=agent_data['username'],
                email=agent_data['email'],
                password='demo123',
                first_name=agent_data['first_name'],
                last_name=agent_data['last_name'],
                is_organisor=False,
                is_agent=True
            )
            agent = Agent.objects.create(
                user=user,
                organisation=organizer.userprofile
            )
            agents.append(agent)
            self.stdout.write(f'Created agent: {agent.email}')

        # Create default categories
        categories = CategoryService.create_default_categories(organizer.userprofile)
        self.stdout.write(f'Created {len(categories)} default categories')

        # Create sample leads
        leads_data = [
            {
                'first_name': 'Alice',
                'last_name': 'Brown',
                'email': 'alice@example.com',
                'phone_number': '+1234567890',
                'age': 28,
                'source': 'Website',
                'description': 'Interested in premium package'
            },
            {
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'email': 'bob@example.com',
                'phone_number': '+1234567891',
                'age': 35,
                'source': 'Referral',
                'description': 'Looking for enterprise solution'
            },
            {
                'first_name': 'Carol',
                'last_name': 'Davis',
                'email': 'carol@example.com',
                'phone_number': '+1234567892',
                'age': 42,
                'source': 'Cold Call',
                'description': 'Budget-conscious customer'
            },
            {
                'first_name': 'David',
                'last_name': 'Miller',
                'email': 'david@example.com',
                'phone_number': '+1234567893',
                'age': 31,
                'source': 'Website',
                'description': 'Technical requirements needed'
            },
            {
                'first_name': 'Eva',
                'last_name': 'Garcia',
                'email': 'eva@example.com',
                'phone_number': '+1234567894',
                'age': 29,
                'source': 'Social Media',
                'description': 'Quick decision maker'
            }
        ]

        # Create leads and assign some to agents
        for i, lead_data in enumerate(leads_data):
            lead = Lead.objects.create(
                first_name=lead_data['first_name'],
                last_name=lead_data['last_name'],
                email=lead_data['email'],
                phone_number=lead_data['phone_number'],
                age=lead_data['age'],
                organisation=organizer.userprofile,
                source=lead_data['source'],
                description=lead_data['description']
            )
            
            # Assign some leads to agents
            if i < len(agents):
                lead.agent = agents[i]
                lead.category = categories[i % len(categories)]
                lead.save()
            
            self.stdout.write(f'Created lead: {lead.full_name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Demo data setup complete!\n'
                f'- 1 Organizer\n'
                f'- {len(agents)} Agents\n'
                f'- {len(categories)} Categories\n'
                f'- {len(leads_data)} Leads\n\n'
                f'Login credentials:\n'
                f'Organizer: organizer@demo.com / demo123\n'
                f'Agents: agent1@demo.com / demo123, agent2@demo.com / demo123, etc.'
            )
        ) 