"""
Management command to set up comprehensive demo data for the Lead Management System.

This command creates realistic sample users, agents, categories, and leads for testing
and demonstration purposes with varied data to showcase the system's capabilities.
"""

import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from leads.models import Lead, Agent, Category
from leads.services import CategoryService

User = get_user_model()


class Command(BaseCommand):
    """Management command to set up comprehensive demo data."""
    
    help = 'Set up comprehensive demo data for the Lead Management System'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating demo data',
        )
        parser.add_argument(
            '--leads',
            type=int,
            default=100,
            help='Number of leads to create (default: 100)',
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

        self.stdout.write('Setting up comprehensive demo data...')
        
        # Create organizer users
        organizers_data = [
            {
                'username': 'admin',
                'email': 'admin@leadflow.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'password': 'admin'
            },
            {
                'username': 'manager',
                'email': 'manager@leadflow.com',
                'first_name': 'Michael',
                'last_name': 'Chen',
                'password': 'manager'
            },
            {
                'username': 'director',
                'email': 'director@leadflow.com',
                'first_name': 'Emily',
                'last_name': 'Rodriguez',
                'password': 'director'
            }
        ]

        organizers = []
        for org_data in organizers_data:
            # Check if user already exists
            user, created = User.objects.get_or_create(
                username=org_data['username'],
                defaults={
                    'email': org_data['email'],
                    'first_name': org_data['first_name'],
                    'last_name': org_data['last_name'],
                    'is_organisor': True,
                    'is_agent': False
                }
            )
            
            if created:
                user.set_password(org_data['password'])
                user.save()
                self.stdout.write(f'Created organizer: {user.email}')
            else:
                # Update existing user if needed
                user.email = org_data['email']
                user.first_name = org_data['first_name']
                user.last_name = org_data['last_name']
                user.is_organisor = True
                user.is_agent = False
                user.set_password(org_data['password'])
                user.save()
                self.stdout.write(f'Updated existing organizer: {user.email}')
            
            organizers.append(user)

        # Create agent users with realistic names
        agents_data = [
            {'username': 'john', 'first_name': 'John', 'last_name': 'Smith', 'email': 'john@leadflow.com'},
            {'username': 'jane', 'first_name': 'Jane', 'last_name': 'Doe', 'email': 'jane@leadflow.com'},
            {'username': 'mike', 'first_name': 'Mike', 'last_name': 'Johnson', 'email': 'mike@leadflow.com'},
            {'username': 'sarah', 'first_name': 'Sarah', 'last_name': 'Williams', 'email': 'sarah@leadflow.com'},
            {'username': 'david', 'first_name': 'David', 'last_name': 'Brown', 'email': 'david@leadflow.com'},
            {'username': 'lisa', 'first_name': 'Lisa', 'last_name': 'Davis', 'email': 'lisa@leadflow.com'},
            {'username': 'james', 'first_name': 'James', 'last_name': 'Miller', 'email': 'james@leadflow.com'},
            {'username': 'emma', 'first_name': 'Emma', 'last_name': 'Wilson', 'email': 'emma@leadflow.com'},
            {'username': 'alex', 'first_name': 'Alex', 'last_name': 'Taylor', 'email': 'alex@leadflow.com'},
            {'username': 'sophia', 'first_name': 'Sophia', 'last_name': 'Anderson', 'email': 'sophia@leadflow.com'},
            {'username': 'daniel', 'first_name': 'Daniel', 'last_name': 'Thomas', 'email': 'daniel@leadflow.com'},
            {'username': 'olivia', 'first_name': 'Olivia', 'last_name': 'Jackson', 'email': 'olivia@leadflow.com'},
            {'username': 'chris', 'first_name': 'Chris', 'last_name': 'White', 'email': 'chris@leadflow.com'},
            {'username': 'amanda', 'first_name': 'Amanda', 'last_name': 'Harris', 'email': 'amanda@leadflow.com'},
            {'username': 'kevin', 'first_name': 'Kevin', 'last_name': 'Martin', 'email': 'kevin@leadflow.com'},
        ]

        agents = []
        for agent_data in agents_data:
            # Check if user already exists
            user, created = User.objects.get_or_create(
                username=agent_data['username'],
                defaults={
                    'email': agent_data['email'],
                    'first_name': agent_data['first_name'],
                    'last_name': agent_data['last_name'],
                    'is_organisor': False,
                    'is_agent': True
                }
            )
            
            if created:
                user.set_password(agent_data['username'])  # Same as username for easy testing
                user.save()
                self.stdout.write(f'Created agent: {user.email}')
            else:
                # Update existing user if needed
                user.email = agent_data['email']
                user.first_name = agent_data['first_name']
                user.last_name = agent_data['last_name']
                user.is_organisor = False
                user.is_agent = True
                user.set_password(agent_data['username'])
                user.save()
                self.stdout.write(f'Updated existing agent: {user.email}')
            
            # Assign agents to different organizers
            organizer = random.choice(organizers)
            agent, agent_created = Agent.objects.get_or_create(
                user=user,
                defaults={'organisation': organizer.userprofile}
            )
            
            if not agent_created:
                agent.organisation = organizer.userprofile
                agent.save()
            
            agents.append(agent)

        # Create comprehensive categories for each organizer
        all_categories = []
        for organizer in organizers:
            categories_data = [
                {'name': 'New Lead', 'color': '#3B82F6'},
                {'name': 'Contacted', 'color': '#F59E0B'},
                {'name': 'Qualified', 'color': '#10B981'},
                {'name': 'Proposal Sent', 'color': '#8B5CF6'},
                {'name': 'Negotiation', 'color': '#EF4444'},
                {'name': 'Converted', 'color': '#059669'},
                {'name': 'Lost', 'color': '#6B7280'},
                {'name': 'Follow Up', 'color': '#F97316'},
                {'name': 'Hot Lead', 'color': '#DC2626'},
                {'name': 'Cold Lead', 'color': '#9CA3AF'},
            ]
            
            for cat_data in categories_data:
                category, created = Category.objects.get_or_create(
                    name=cat_data['name'],
                    organisation=organizer.userprofile,
                    defaults={'color': cat_data['color']}
                )
                if not created:
                    category.color = cat_data['color']
                    category.save()
                all_categories.append(category)
        
        self.stdout.write(f'Created/Updated {len(all_categories)} categories')

        # Realistic lead data
        first_names = [
            'Alice', 'Bob', 'Carol', 'David', 'Eva', 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack',
            'Kate', 'Liam', 'Mia', 'Noah', 'Olivia', 'Paul', 'Quinn', 'Rachel', 'Sam', 'Tina',
            'Uma', 'Victor', 'Wendy', 'Xavier', 'Yara', 'Zoe', 'Adam', 'Bella', 'Carl', 'Diana',
            'Ethan', 'Fiona', 'George', 'Hannah', 'Ian', 'Julia', 'Kyle', 'Laura', 'Mark', 'Nina',
            'Oscar', 'Penny', 'Quentin', 'Rose', 'Steve', 'Tara', 'Ulysses', 'Vera', 'Walter', 'Xena'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
            'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
            'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
            'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker'
        ]
        
        companies = [
            'TechCorp', 'InnovateSoft', 'DataFlow', 'CloudTech', 'Digital Solutions',
            'Future Systems', 'Smart Analytics', 'CyberNet', 'WebWorks', 'AppFactory',
            'CodeCraft', 'DevStudio', 'TechBridge', 'Innovation Labs', 'Digital Dynamics',
            'Cloud Solutions', 'DataWorks', 'Tech Innovations', 'Smart Systems', 'Future Tech',
            'Digital Creations', 'Web Solutions', 'App Development', 'Code Solutions', 'Dev Works',
            'Tech Solutions', 'Innovation Tech', 'Digital Works', 'Cloud Systems', 'Data Solutions'
        ]
        
        sources = [
            'Website', 'Referral', 'Cold Call', 'Social Media', 'Email Campaign',
            'Trade Show', 'LinkedIn', 'Google Ads', 'Facebook Ads', 'Content Marketing',
            'Partner Referral', 'Direct Mail', 'Telemarketing', 'Online Search', 'Word of Mouth',
            'Industry Event', 'Webinar', 'Blog Post', 'Press Release', 'Customer Referral'
        ]
        
        descriptions = [
            'Interested in enterprise solution for 500+ employees',
            'Looking for cloud migration services',
            'Needs custom software development',
            'Wants to improve customer experience',
            'Seeking data analytics implementation',
            'Interested in AI and machine learning solutions',
            'Needs cybersecurity assessment',
            'Looking for mobile app development',
            'Wants to automate business processes',
            'Interested in digital transformation',
            'Needs e-commerce platform development',
            'Looking for CRM system implementation',
            'Wants to improve website performance',
            'Interested in blockchain solutions',
            'Needs API integration services',
            'Looking for cloud infrastructure setup',
            'Wants to implement DevOps practices',
            'Interested in IoT solutions',
            'Needs data backup and recovery',
            'Looking for IT consulting services'
        ]

        # Create leads
        num_leads = options['leads']
        leads_created = 0
        
        for i in range(num_leads):
            # Random data generation
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            age = random.randint(25, 65)
            company = random.choice(companies)
            source = random.choice(sources)
            description = random.choice(descriptions)
            
            # Generate realistic email
            email = f"{first_name.lower()}.{last_name.lower()}@{company.lower().replace(' ', '')}.com"
            
            # Generate realistic phone number
            phone = f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"
            
            # Random organization assignment
            organizer = random.choice(organizers)
            
            # Check if lead with this email already exists
            if Lead.objects.filter(email=email).exists():
                continue  # Skip if lead already exists
            
            # Create lead
            lead = Lead.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone,
                age=age,
                organisation=organizer.userprofile,
                source=source,
                description=f"{description} - {company}"
            )
            
            # Randomly assign agent and category
            if random.random() < 0.7:  # 70% chance of being assigned to an agent
                # Get agents from the same organization
                org_agents = [agent for agent in agents if agent.organisation == organizer.userprofile]
                if org_agents:
                    lead.agent = random.choice(org_agents)
            
            # Assign category
            org_categories = [cat for cat in all_categories if cat.organisation == organizer.userprofile]
            if org_categories:
                lead.category = random.choice(org_categories)
            
            # Set random dates for more realism
            days_ago = random.randint(0, 90)
            lead.date_added = timezone.now() - timedelta(days=days_ago)
            lead.save()
            
            # Set last contacted for some leads
            if lead.agent and random.random() < 0.6:
                contact_days_ago = random.randint(0, days_ago)
                lead.last_contacted = timezone.now() - timedelta(days=contact_days_ago)
                lead.save()
            
            leads_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Comprehensive demo data setup complete!\n'
                f'- {len(organizers)} Organizers\n'
                f'- {len(agents)} Agents\n'
                f'- {len(all_categories)} Categories\n'
                f'- {leads_created} Leads created\n\n'
                f'Login credentials (username = password):\n'
                f'Organizers: admin/admin, manager/manager, director/director\n'
                f'Agents: john/john, jane/jane, mike/mike, sarah/sarah, david/david, etc.\n\n'
                f'All agents have the same username and password for easy testing!'
            )
        ) 