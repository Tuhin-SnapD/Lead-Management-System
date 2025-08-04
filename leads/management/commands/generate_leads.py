"""
Django management command to generate sample leads.

Usage:
    python manage.py generate_leads
    python manage.py generate_leads --count 50
    python manage.py generate_leads --count 100 --organisation admin
"""

import random
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from leads.models import Lead, Category, Agent, UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate sample leads with realistic data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=25,
            help='Number of leads to generate (default: 25)'
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
            help='Clear existing leads before generating new ones'
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

            # Sample data for generating realistic leads
            first_names = [
                'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Jessica',
                'William', 'Ashley', 'Christopher', 'Amanda', 'James', 'Stephanie', 'Daniel',
                'Nicole', 'Matthew', 'Elizabeth', 'Anthony', 'Megan', 'Mark', 'Lauren',
                'Donald', 'Rachel', 'Steven', 'Kayla', 'Paul', 'Amber', 'Andrew', 'Brittany',
                'Joshua', 'Danielle', 'Kenneth', 'Melissa', 'Kevin', 'Christina', 'Brian',
                'Heather', 'George', 'Tiffany', 'Timothy', 'Kimberly', 'Ronald', 'Crystal',
                'Jason', 'Michelle', 'Edward', 'Jennifer', 'Jeffrey', 'Laura', 'Ryan',
                'Lisa', 'Jacob', 'Stephanie', 'Gary', 'Nicole', 'Nicholas', 'Shannon',
                'Eric', 'Angela', 'Jonathan', 'Rebecca', 'Stephen', 'Samantha', 'Larry',
                'Christine', 'Justin', 'Catherine', 'Scott', 'Virginia', 'Brandon', 'Debra',
                'Benjamin', 'Rachel', 'Frank', 'Carolyn', 'Gregory', 'Janet', 'Raymond',
                'Maria', 'Samuel', 'Heather', 'Patrick', 'Diane', 'Alexander', 'Julie',
                'Jack', 'Joyce', 'Dennis', 'Victoria', 'Jerry', 'Kelly', 'Tyler', 'Christina',
                'Aaron', 'Joan', 'Jose', 'Evelyn', 'Adam', 'Lauren', 'Nathan', 'Judith',
                'Henry', 'Megan', 'Douglas', 'Cheryl', 'Zachary', 'Andrea', 'Peter', 'Hannah',
                'Kyle', 'Jacqueline', 'Walter', 'Martha', 'Ethan', 'Gloria', 'Jeremy', 'Teresa'
            ]

            last_names = [
                'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
                'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
                'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
                'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
                'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
                'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker',
                'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales', 'Murphy',
                'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson', 'Bailey',
                'Reed', 'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward', 'Richardson', 'Watson',
                'Brooks', 'Chavez', 'Wood', 'James', 'Bennett', 'Gray', 'Mendoza', 'Ruiz', 'Hughes',
                'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers', 'Long', 'Ross',
                'Foster', 'Jimenez', 'Powell', 'Jenkins', 'Perry', 'Russell', 'Sullivan', 'Bell',
                'Coleman', 'Butler', 'Henderson', 'Barnes', 'Gonzales', 'Fisher', 'Vasquez',
                'Simmons', 'Romero', 'Jordan', 'Patterson', 'Alexander', 'Hamilton', 'Graham',
                'Reynolds', 'Griffin', 'Wallace', 'Moreno', 'West', 'Cole', 'Hayes', 'Bryant',
                'Herrera', 'Gibson', 'Ellis', 'Tran', 'Medina', 'Aguilar', 'Stevens', 'Murray',
                'Ford', 'Castro', 'Marshall', 'Owens', 'Harrison', 'Fernandez', 'Mcdonald',
                'Woods', 'Washington', 'Kennedy', 'Wells', 'Vargas', 'Henry', 'Chen', 'Freeman',
                'Webb', 'Tucker', 'Guzman', 'Burns', 'Crawford', 'Olson', 'Simpson', 'Porter',
                'Hunter', 'Gordon', 'Mendez', 'Silva', 'Shaw', 'Snyder', 'Mason', 'Dixon',
                'Muñoz', 'Hunt', 'Hicks', 'Holmes', 'Palmer', 'Wagner', 'Black', 'Robertson',
                'Boyd', 'Rose', 'Stone', 'Salazar', 'Fox', 'Warren', 'Mills', 'Meyer', 'Rice',
                'Schmidt', 'Garza', 'Daniels', 'Ferguson', 'Nichols', 'Stephens', 'Soto',
                'Weaver', 'Ryan', 'Gardner', 'Payne', 'Grant', 'Dunn', 'Kelley', 'Spencer'
            ]

            companies = [
                'TechCorp Solutions', 'Global Innovations Inc', 'Digital Dynamics', 'Future Systems',
                'Smart Solutions Ltd', 'Innovation Hub', 'TechStart Pro', 'Digital Ventures',
                'NextGen Technologies', 'Cloud Solutions Inc', 'DataFlow Systems', 'CyberTech Pro',
                'InnovateSoft', 'TechBridge Solutions', 'Digital Edge Corp', 'FutureTech Labs',
                'SmartBridge Inc', 'Innovation Partners', 'TechFlow Systems', 'Digital Peak',
                'NextWave Technologies', 'CloudBridge Solutions', 'DataTech Pro', 'CyberSoft Inc',
                'InnovateHub', 'TechSolutions Pro', 'Digital Dynamics Inc', 'FutureBridge',
                'SmartTech Labs', 'Innovation Systems', 'TechPeak Solutions', 'DigitalFlow Pro',
                'NextGen Bridge', 'CloudTech Inc', 'DataSolutions Pro', 'CyberBridge Systems',
                'InnovateSoft Pro', 'TechHub Solutions', 'DigitalPeak Inc', 'FutureFlow Pro',
                'SmartBridge Technologies', 'Innovation Labs', 'TechSolutions Inc', 'DigitalBridge Pro',
                'NextWave Systems', 'CloudPeak Solutions', 'DataBridge Inc', 'CyberHub Pro',
                'InnovateFlow Systems', 'TechPeak Inc', 'DigitalSolutions Pro', 'FutureBridge Labs'
            ]

            sources = [
                'Website', 'Referral', 'Cold Call', 'Social Media', 'Email Campaign', 'Trade Show',
                'LinkedIn', 'Google Ads', 'Facebook Ads', 'Twitter', 'Instagram', 'YouTube',
                'Blog', 'Newsletter', 'Partner', 'Customer Referral', 'Online Search', 'Direct Mail',
                'Telemarketing', 'Webinar', 'Conference', 'Industry Event', 'Press Release',
                'Content Marketing', 'SEO', 'PPC', 'Affiliate', 'Influencer', 'Podcast', 'Video'
            ]

            descriptions = [
                'Interested in our enterprise solutions for large organizations.',
                'Looking for scalable cloud infrastructure for their growing business.',
                'Seeking digital transformation consulting services.',
                'Wants to implement AI-powered analytics platform.',
                'Needs cybersecurity solutions for their financial services.',
                'Interested in mobile app development for their startup.',
                'Looking for data migration and integration services.',
                'Wants to modernize their legacy systems.',
                'Seeking e-commerce platform development.',
                'Needs customer relationship management implementation.',
                'Interested in business intelligence and reporting tools.',
                'Looking for DevOps and automation solutions.',
                'Wants to implement blockchain technology.',
                'Seeking IoT platform development.',
                'Needs machine learning model deployment.',
                'Interested in API development and integration.',
                'Looking for cloud-native application development.',
                'Wants to implement microservices architecture.',
                'Seeking data warehouse and analytics solutions.',
                'Needs mobile-first responsive web applications.',
                'Interested in real-time data processing systems.',
                'Looking for automated testing and quality assurance.',
                'Wants to implement CI/CD pipeline solutions.',
                'Seeking enterprise resource planning integration.',
                'Needs customer support and helpdesk systems.',
                'Interested in marketing automation platforms.',
                'Looking for sales force automation tools.',
                'Wants to implement project management solutions.',
                'Seeking human resources management systems.',
                'Needs inventory and supply chain management.',
                'Interested in financial management and accounting software.',
                'Looking for healthcare information systems.',
                'Wants to implement educational technology platforms.',
                'Seeking retail management and POS systems.',
                'Needs hospitality and tourism management solutions.',
                'Interested in real estate management platforms.',
                'Looking for legal practice management software.',
                'Wants to implement construction project management.',
                'Seeking manufacturing execution systems.',
                'Needs logistics and transportation management.',
                'Interested in energy management and monitoring.',
                'Looking for environmental compliance tracking.',
                'Wants to implement quality management systems.',
                'Seeking risk management and compliance platforms.',
                'Needs asset management and maintenance systems.',
                'Interested in fleet management solutions.',
                'Looking for warehouse management systems.',
                'Wants to implement customer experience platforms.',
                'Seeking employee engagement and communication tools.',
                'Needs performance management and analytics.',
                'Interested in learning management systems.',
                'Looking for talent acquisition and recruitment platforms.'
            ]

            # Get or create categories
            categories = []
            category_names = ['New', 'Contacted', 'Qualified', 'Proposal', 'Negotiation', 'Converted', 'Lost']
            category_colors = ['#3B82F6', '#F59E0B', '#10B981', '#8B5CF6', '#EF4444', '#059669', '#6B7280']
            
            for name, color in zip(category_names, category_colors):
                category, created = Category.objects.get_or_create(
                    name=name,
                    organisation=organisation,
                    defaults={'color': color}
                )
                categories.append(category)

            # Get agents if they exist
            agents = list(Agent.objects.filter(organisation=organisation, is_active=True))
            
            # Clear existing leads if requested
            if clear_existing:
                Lead.objects.filter(organisation=organisation).delete()
                self.stdout.write(
                    self.style.WARNING(f'Cleared {count} existing leads for organisation "{org_username}"')
                )

            # Generate leads
            leads_created = 0
            with transaction.atomic():
                for i in range(count):
                    # Generate random lead data
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    age = random.randint(25, 65)
                    email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'company.com'])}"
                    phone = f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"
                    
                    # Random lead details
                    source = random.choice(sources)
                    description = random.choice(descriptions)
                    
                    # Random lead score (0-100)
                    lead_score = random.randint(0, 100)
                    
                    # Random engagement level
                    engagement_levels = ['low', 'medium', 'high']
                    engagement_level = random.choice(engagement_levels)
                    
                    # Random category (weighted towards New and Contacted)
                    category_weights = [0.4, 0.3, 0.1, 0.05, 0.05, 0.05, 0.05]  # More weight to early stages
                    category = random.choices(categories, weights=category_weights)[0]
                    
                    # Random agent assignment (30% chance)
                    agent = random.choice(agents) if agents and random.random() < 0.3 else None
                    
                    # Random dates
                    days_ago = random.randint(0, 365)
                    date_added = timezone.now() - timedelta(days=days_ago)
                    
                    # Random follow-up date (20% chance)
                    follow_up_date = None
                    if random.random() < 0.2:
                        follow_up_days = random.randint(1, 30)
                        follow_up_date = timezone.now() + timedelta(days=follow_up_days)
                    
                    # Random snooze (5% chance)
                    is_snoozed = random.random() < 0.05
                    snooze_until = None
                    if is_snoozed:
                        snooze_days = random.randint(1, 14)
                        snooze_until = timezone.now() + timedelta(days=snooze_days)
                    
                    # Random interaction count
                    interaction_count = random.randint(0, 10)
                    
                    # Create the lead
                    lead = Lead.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        age=age,
                        email=email,
                        phone_number=phone,
                        organisation=organisation,
                        agent=agent,
                        category=category,
                        description=description,
                        source=source,
                        lead_score=lead_score,
                        engagement_level=engagement_level,
                        follow_up_date=follow_up_date,
                        is_snoozed=is_snoozed,
                        snooze_until=snooze_until,
                        interaction_count=interaction_count,
                        date_added=date_added
                    )
                    
                    leads_created += 1
                    
                    if leads_created % 10 == 0:
                        self.stdout.write(f'Created {leads_created} leads...')

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {leads_created} leads for organisation "{org_username}"\n'
                    f'Categories created: {len(categories)}\n'
                    f'Agents available: {len(agents)}'
                )
            )

        except Exception as e:
            raise CommandError(f'Failed to generate leads: {str(e)}') 