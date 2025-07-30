"""
Tests for Lead Management Models

This module contains tests for the lead management system models,
including User, Lead, Agent, and Category models.
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from leads.models import Lead, Agent, Category, UserProfile
from leads.services import LeadService, AgentService, CategoryService

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the User model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation(self):
        """Test user creation with proper fields."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.is_organisor)
        self.assertFalse(self.user.is_agent)
    
    def test_user_full_name_property(self):
        """Test the full_name property."""
        self.assertEqual(self.user.full_name, 'Test User')
        
        # Test with empty names
        self.user.first_name = ''
        self.user.last_name = ''
        self.assertEqual(self.user.full_name, 'testuser')
    
    def test_userprofile_creation_signal(self):
        """Test that UserProfile is created automatically."""
        self.assertTrue(hasattr(self.user, 'userprofile'))
        self.assertIsInstance(self.user.userprofile, UserProfile)


class LeadModelTest(TestCase):
    """Test cases for the Lead model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='organisor',
            email='organisor@example.com',
            password='testpass123'
        )
        self.agent_user = User.objects.create_user(
            username='agent',
            email='agent@example.com',
            password='testpass123',
            is_organisor=False,
            is_agent=True
        )
        self.agent = Agent.objects.create(
            user=self.agent_user,
            organisation=self.user.userprofile
        )
        self.category = Category.objects.create(
            name='New',
            organisation=self.user.userprofile
        )
    
    def test_lead_creation(self):
        """Test lead creation with valid data."""
        lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            age=30,
            email='john@example.com',
            phone_number='+1234567890',
            organisation=self.user.userprofile,
            description='Test lead'
        )
        
        self.assertEqual(lead.full_name, 'John Doe')
        self.assertEqual(lead.email, 'john@example.com')
        self.assertFalse(lead.is_assigned)
        self.assertFalse(lead.is_categorized)
    
    def test_lead_validation(self):
        """Test lead field validation."""
        # Test invalid email
        with self.assertRaises(ValidationError):
            lead = Lead(
                first_name='John',
                last_name='Doe',
                age=30,
                email='invalid-email',
                phone_number='+1234567890',
                organisation=self.user.userprofile
            )
            lead.full_clean()
        
        # Test invalid age
        with self.assertRaises(ValidationError):
            lead = Lead(
                first_name='John',
                last_name='Doe',
                age=-5,
                email='john@example.com',
                phone_number='+1234567890',
                organisation=self.user.userprofile
            )
            lead.full_clean()
    
    def test_lead_agent_assignment(self):
        """Test agent assignment to lead."""
        lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            age=30,
            email='john@example.com',
            phone_number='+1234567890',
            organisation=self.user.userprofile
        )
        
        lead.assign_agent(self.agent)
        self.assertTrue(lead.is_assigned)
        self.assertEqual(lead.agent, self.agent)
    
    def test_lead_category_update(self):
        """Test category update for lead."""
        lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            age=30,
            email='john@example.com',
            phone_number='+1234567890',
            organisation=self.user.userprofile
        )
        
        lead.update_category(self.category)
        self.assertTrue(lead.is_categorized)
        self.assertEqual(lead.category, self.category)
    
    def test_lead_mark_contacted(self):
        """Test marking lead as contacted."""
        lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            age=30,
            email='john@example.com',
            phone_number='+1234567890',
            organisation=self.user.userprofile
        )
        
        lead.mark_contacted()
        self.assertIsNotNone(lead.last_contacted)


class AgentModelTest(TestCase):
    """Test cases for the Agent model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='organisor',
            email='organisor@example.com',
            password='testpass123'
        )
        self.agent_user = User.objects.create_user(
            username='agent',
            email='agent@example.com',
            password='testpass123',
            is_organisor=False,
            is_agent=True
        )
    
    def test_agent_creation(self):
        """Test agent creation."""
        agent = Agent.objects.create(
            user=self.agent_user,
            organisation=self.user.userprofile
        )
        
        self.assertEqual(agent.user, self.agent_user)
        self.assertEqual(agent.organisation, self.user.userprofile)
        self.assertTrue(agent.is_active)
    
    def test_agent_properties(self):
        """Test agent properties."""
        agent = Agent.objects.create(
            user=self.agent_user,
            organisation=self.user.userprofile
        )
        
        self.assertEqual(agent.full_name, 'agent')
        self.assertEqual(agent.email, 'agent@example.com')


class CategoryModelTest(TestCase):
    """Test cases for the Category model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='organisor',
            email='organisor@example.com',
            password='testpass123'
        )
    
    def test_category_creation(self):
        """Test category creation."""
        category = Category.objects.create(
            name='New',
            organisation=self.user.userprofile,
            color='#3B82F6'
        )
        
        self.assertEqual(category.name, 'New')
        self.assertEqual(category.organisation, self.user.userprofile)
        self.assertEqual(category.color, '#3B82F6')
    
    def test_category_unique_constraint(self):
        """Test category unique constraint within organization."""
        Category.objects.create(
            name='New',
            organisation=self.user.userprofile
        )
        
        # Should not be able to create another category with same name
        with self.assertRaises(Exception):
            Category.objects.create(
                name='New',
                organisation=self.user.userprofile
            )


class LeadServiceTest(TestCase):
    """Test cases for the LeadService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='organisor',
            email='organisor@example.com',
            password='testpass123'
        )
        self.agent_user = User.objects.create_user(
            username='agent',
            email='agent@example.com',
            password='testpass123',
            is_organisor=False,
            is_agent=True
        )
        self.agent = Agent.objects.create(
            user=self.agent_user,
            organisation=self.user.userprofile
        )
        self.category = Category.objects.create(
            name='New',
            organisation=self.user.userprofile
        )
    
    def test_create_lead_service(self):
        """Test lead creation through service."""
        lead = LeadService.create_lead(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='+1234567890',
            age=30,
            organisation=self.user.userprofile,
            description='Test lead'
        )
        
        self.assertEqual(lead.full_name, 'John Doe')
        self.assertEqual(lead.organisation, self.user.userprofile)
    
    def test_assign_agent_service(self):
        """Test agent assignment through service."""
        lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            age=30,
            email='john@example.com',
            phone_number='+1234567890',
            organisation=self.user.userprofile
        )
        
        success = LeadService.assign_agent_to_lead(lead, self.agent)
        self.assertTrue(success)
        self.assertEqual(lead.agent, self.agent)
    
    def test_get_lead_statistics(self):
        """Test lead statistics calculation."""
        # Create some test leads
        Lead.objects.create(
            first_name='John',
            last_name='Doe',
            age=30,
            email='john@example.com',
            phone_number='+1234567890',
            organisation=self.user.userprofile
        )
        
        Lead.objects.create(
            first_name='Jane',
            last_name='Smith',
            age=25,
            email='jane@example.com',
            phone_number='+1234567891',
            organisation=self.user.userprofile,
            agent=self.agent
        )
        
        stats = LeadService.get_lead_statistics(self.user.userprofile)
        
        self.assertEqual(stats['total_leads'], 2)
        self.assertEqual(stats['assigned_leads'], 1)
        self.assertEqual(stats['unassigned_leads'], 1)


class AgentServiceTest(TestCase):
    """Test cases for the AgentService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='organisor',
            email='organisor@example.com',
            password='testpass123'
        )
    
    def test_create_agent_service(self):
        """Test agent creation through service."""
        agent = AgentService.create_agent(
            email='newagent@example.com',
            first_name='New',
            last_name='Agent',
            organisation=self.user.userprofile
        )
        
        self.assertEqual(agent.email, 'newagent@example.com')
        self.assertEqual(agent.full_name, 'New Agent')
        self.assertTrue(agent.user.is_agent)
        self.assertFalse(agent.user.is_organisor)
    
    def test_get_agent_performance(self):
        """Test agent performance calculation."""
        agent_user = User.objects.create_user(
            username='agent',
            email='agent@example.com',
            password='testpass123',
            is_organisor=False,
            is_agent=True
        )
        agent = Agent.objects.create(
            user=agent_user,
            organisation=self.user.userprofile
        )
        
        # Create some test leads
        Lead.objects.create(
            first_name='John',
            last_name='Doe',
            age=30,
            email='john@example.com',
            phone_number='+1234567890',
            organisation=self.user.userprofile,
            agent=agent
        )
        
        performance = AgentService.get_agent_performance(agent)
        
        self.assertEqual(performance['total_leads'], 1)
        self.assertEqual(performance['assigned_leads'], 1)


class CategoryServiceTest(TestCase):
    """Test cases for the CategoryService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='organisor',
            email='organisor@example.com',
            password='testpass123'
        )
    
    def test_create_default_categories(self):
        """Test default category creation."""
        categories = CategoryService.create_default_categories(self.user.userprofile)
        
        self.assertEqual(len(categories), 4)
        category_names = [cat.name for cat in categories]
        self.assertIn('New', category_names)
        self.assertIn('Contacted', category_names)
        self.assertIn('Converted', category_names)
        self.assertIn('Unconverted', category_names)
    
    def test_get_category_statistics(self):
        """Test category statistics calculation."""
        category = Category.objects.create(
            name='New',
            organisation=self.user.userprofile
        )
        
        # Create a lead in this category
        Lead.objects.create(
            first_name='John',
            last_name='Doe',
            age=30,
            email='john@example.com',
            phone_number='+1234567890',
            organisation=self.user.userprofile,
            category=category
        )
        
        stats = CategoryService.get_category_statistics(self.user.userprofile)
        
        self.assertIn('New', stats)
        self.assertEqual(stats['New']['count'], 1) 