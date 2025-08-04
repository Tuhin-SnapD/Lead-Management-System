"""
Celery tasks for Lead Management System.

This module contains background tasks for automated processes
including follow-up reminders, lead scoring updates, and performance tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.conf import settings

from .models import Lead, LeadInteraction, AgentPerformance, Agent
from .ml_service import lead_scoring_service

logger = logging.getLogger(__name__)

# Conditional Celery import
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Create a dummy decorator when Celery is not available
    def shared_task(func):
        return func


@shared_task
def update_lead_scores_task() -> Dict[str, Any]:
    """
    Update lead scores for all organizations using ML model.
    
    Returns:
        Dictionary with task results
    """
    try:
        from .models import UserProfile
        
        results = {}
        total_updated = 0
        
        # Get all organizations
        organizations = UserProfile.objects.all()
        
        for org in organizations:
            try:
                updated_count = lead_scoring_service.update_all_lead_scores(org.id)
                results[org.id] = updated_count
                total_updated += updated_count
                logger.info(f"Updated {updated_count} leads for organization {org.id}")
            except Exception as e:
                logger.error(f"Error updating leads for organization {org.id}: {str(e)}")
                results[org.id] = {'error': str(e)}
        
        logger.info(f"Lead scoring task completed. Total leads updated: {total_updated}")
        return {
            'status': 'success',
            'total_updated': total_updated,
            'organization_results': results
        }
        
    except Exception as e:
        logger.error(f"Error in lead scoring task: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_follow_up_reminders_task() -> Dict[str, Any]:
    """
    Send follow-up reminders for leads with upcoming or overdue follow-ups.
    
    Returns:
        Dictionary with task results
    """
    try:
        now = timezone.now()
        tomorrow = now + timedelta(days=1)
        
        # Get leads with follow-ups due today or overdue
        leads_with_followups = Lead.objects.filter(
            Q(follow_up_date__lte=tomorrow) &
            Q(follow_up_date__gte=now - timedelta(days=7)) &  # Don't send for very old follow-ups
            Q(agent__isnull=False) &
            Q(is_snoozed=False)
        ).select_related('agent__user', 'organisation__user')
        
        sent_count = 0
        failed_count = 0
        
        for lead in leads_with_followups:
            try:
                # Send email to agent
                subject = f"Follow-up Reminder: {lead.full_name}"
                
                context = {
                    'lead': lead,
                    'agent': lead.agent,
                    'is_overdue': lead.follow_up_date < now,
                    'follow_up_date': lead.follow_up_date,
                    'follow_up_notes': lead.follow_up_notes,
                }
                
                html_message = render_to_string('leads/email/follow_up_reminder.html', context)
                plain_message = render_to_string('leads/email/follow_up_reminder.txt', context)
                
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[lead.agent.user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                sent_count += 1
                logger.info(f"Sent follow-up reminder for lead {lead.id} to agent {lead.agent.user.email}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send follow-up reminder for lead {lead.id}: {str(e)}")
        
        logger.info(f"Follow-up reminders task completed. Sent: {sent_count}, Failed: {failed_count}")
        return {
            'status': 'success',
            'sent_count': sent_count,
            'failed_count': failed_count
        }
        
    except Exception as e:
        logger.error(f"Error in follow-up reminders task: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def check_snooze_expiration_task() -> Dict[str, Any]:
    """
    Check for expired snoozes and unsnooze leads.
    
    Returns:
        Dictionary with task results
    """
    try:
        now = timezone.now()
        
        # Get leads with expired snoozes
        expired_snoozes = Lead.objects.filter(
            is_snoozed=True,
            snooze_until__lt=now
        )
        
        unsnoozed_count = 0
        
        for lead in expired_snoozes:
            try:
                lead.unsnooze_lead()
                unsnoozed_count += 1
                logger.info(f"Unsnoozed lead {lead.id}")
            except Exception as e:
                logger.error(f"Error unsnoozing lead {lead.id}: {str(e)}")
        
        logger.info(f"Snooze expiration task completed. Unsnoozed: {unsnoozed_count}")
        return {
            'status': 'success',
            'unsnoozed_count': unsnoozed_count
        }
        
    except Exception as e:
        logger.error(f"Error in snooze expiration task: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def update_agent_performance_task() -> Dict[str, Any]:
    """
    Update agent performance metrics.
    
    Returns:
        Dictionary with task results
    """
    try:
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get all active agents
        agents = Agent.objects.filter(is_active=True)
        
        updated_count = 0
        
        for agent in agents:
            try:
                # Get or create performance record for yesterday
                performance, created = AgentPerformance.objects.get_or_create(
                    agent=agent,
                    date=yesterday,
                    defaults={
                        'leads_assigned': 0,
                        'leads_contacted': 0,
                        'leads_converted': 0,
                        'total_interactions': 0,
                        'average_response_time_hours': 0.0,
                    }
                )
                
                # Calculate metrics for yesterday
                yesterday_start = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
                yesterday_end = timezone.make_aware(datetime.combine(yesterday, datetime.max.time()))
                
                # Leads assigned yesterday
                leads_assigned = agent.assigned_leads.filter(
                    date_added__range=(yesterday_start, yesterday_end)
                ).count()
                
                # Leads contacted yesterday
                leads_contacted = agent.assigned_leads.filter(
                    last_contacted__range=(yesterday_start, yesterday_end)
                ).count()
                
                # Leads converted yesterday
                leads_converted = agent.assigned_leads.filter(
                    category__name__icontains='converted',
                    updated_at__range=(yesterday_start, yesterday_end)
                ).count()
                
                # Total interactions yesterday
                total_interactions = agent.lead_interactions.filter(
                    created_at__range=(yesterday_start, yesterday_end)
                ).count()
                
                # Average response time (simplified calculation)
                avg_response_time = agent.lead_interactions.filter(
                    created_at__range=(yesterday_start, yesterday_end)
                ).aggregate(avg_duration=Avg('duration_minutes'))['avg_duration'] or 0.0
                
                # Update performance record
                performance.leads_assigned = leads_assigned
                performance.leads_contacted = leads_contacted
                performance.leads_converted = leads_converted
                performance.total_interactions = total_interactions
                performance.average_response_time_hours = avg_response_time / 60.0  # Convert to hours
                
                performance.calculate_metrics()
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Error updating performance for agent {agent.id}: {str(e)}")
        
        logger.info(f"Agent performance task completed. Updated: {updated_count}")
        return {
            'status': 'success',
            'updated_count': updated_count
        }
        
    except Exception as e:
        logger.error(f"Error in agent performance task: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def train_ml_model_task(organisation_id: int) -> Dict[str, Any]:
    """
    Train the machine learning model for a specific organization.
    
    Args:
        organisation_id: ID of the organization
        
    Returns:
        Dictionary with training results
    """
    try:
        results = lead_scoring_service.train_model(organisation_id)
        logger.info(f"ML model training completed for organization {organisation_id}")
        return {
            'status': 'success',
            'organisation_id': organisation_id,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error training ML model for organization {organisation_id}: {str(e)}")
        return {
            'status': 'error',
            'organisation_id': organisation_id,
            'message': str(e)
        }


@shared_task
def send_calendar_invite_task(lead_id: int, agent_id: int, meeting_date: str, duration_minutes: int = 60) -> Dict[str, Any]:
    """
    Send calendar invite for a meeting with a lead.
    
    Args:
        lead_id: ID of the lead
        agent_id: ID of the agent
        meeting_date: ISO format date string
        duration_minutes: Duration of the meeting in minutes
        
    Returns:
        Dictionary with task results
    """
    try:
        from icalendar import Calendar, Event
        from datetime import datetime
        
        lead = Lead.objects.get(id=lead_id)
        agent = Agent.objects.get(id=agent_id)
        
        # Create calendar event
        cal = Calendar()
        cal.add('prodid', '-//Lead Management System//Calendar Event//')
        cal.add('version', '2.0')
        
        event = Event()
        event.add('summary', f'Meeting with {lead.full_name}')
        event.add('description', f'Follow-up meeting with {lead.full_name}\n\nLead Details:\nEmail: {lead.email}\nPhone: {lead.phone_number}\n\nAgent: {agent.full_name}')
        
        # Parse meeting date
        meeting_datetime = datetime.fromisoformat(meeting_date.replace('Z', '+00:00'))
        event.add('dtstart', meeting_datetime)
        event.add('dtend', meeting_datetime + timedelta(minutes=duration_minutes))
        event.add('dtstamp', datetime.now())
        
        # Add attendees
        event.add('attendee', f'MAILTO:{lead.email}')
        event.add('attendee', f'MAILTO:{agent.user.email}')
        
        cal.add_component(event)
        
        # Send calendar invite via email
        subject = f"Meeting Invitation: {lead.full_name}"
        
        context = {
            'lead': lead,
            'agent': agent,
            'meeting_date': meeting_datetime,
            'duration_minutes': duration_minutes,
        }
        
        html_message = render_to_string('leads/email/calendar_invite.html', context)
        plain_message = render_to_string('leads/email/calendar_invite.txt', context)
        
        # Send to lead
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[lead.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Send to agent
        send_mail(
            subject=f"Calendar Invite Sent: {lead.full_name}",
            message=f"Calendar invite sent to {lead.full_name} for {meeting_datetime.strftime('%Y-%m-%d %H:%M')}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[agent.user.email],
            fail_silently=False,
        )
        
        logger.info(f"Calendar invite sent for lead {lead_id} with agent {agent_id}")
        return {
            'status': 'success',
            'lead_id': lead_id,
            'agent_id': agent_id,
            'meeting_date': meeting_date
        }
        
    except Exception as e:
        logger.error(f"Error sending calendar invite: {str(e)}")
        return {'status': 'error', 'message': str(e)} 