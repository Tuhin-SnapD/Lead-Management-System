from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import User, Lead, Agent, UserProfile, Category, LeadInteraction, AgentPerformance, LeadSource


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'organisation', 'color_display', 'lead_count', 'created_at')
    list_filter = ('organisation', 'created_at')
    search_fields = ('name', 'organisation__user__username')
    readonly_fields = ('created_at',)
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'organisation', 'color')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
                obj.color,
                obj.color
            )
        return '-'
    color_display.short_description = 'Color'

    def lead_count(self, obj):
        return obj.leads.count()
    lead_count.short_description = 'Leads'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_organisor', 'is_agent', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_organisor', 'is_agent', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Lead Management'), {
            'fields': ('is_organisor', 'is_agent'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_organisor', 'is_agent'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organisation_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def organisation_name(self, obj):
        return obj.user.username if obj.user else '-'
    organisation_name.short_description = 'Organisation'


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone_number', 'agent_display', 'category_display', 'organisation', 'date_added', 'status_display')
    list_filter = ('agent', 'category', 'organisation', 'date_added', 'source')
    search_fields = ('first_name', 'last_name', 'email', 'phone_number', 'agent__user__username')
    readonly_fields = ('date_added', 'last_contacted')
    ordering = ('-date_added',)
    date_hierarchy = 'date_added'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'age', 'email', 'phone_number')
        }),
        ('Lead Details', {
            'fields': ('description', 'source', 'organisation')
        }),
        ('Assignment', {
            'fields': ('agent', 'category')
        }),
        ('Timestamps', {
            'fields': ('date_added', 'last_contacted'),
            'classes': ('collapse',)
        }),
    )

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'
    full_name.admin_order_field = 'first_name'

    def agent_display(self, obj):
        if obj.agent:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:leads_agent_change', args=[obj.agent.id]),
                obj.agent.user.get_full_name() or obj.agent.user.username
            )
        return format_html('<span style="color: #ef4444;">Unassigned</span>')
    agent_display.short_description = 'Agent'

    def category_display(self, obj):
        if obj.category:
            return format_html(
                '<span style="background-color: {}20; color: {}; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
                obj.category.color,
                obj.category.color,
                obj.category.name
            )
        return '-'
    category_display.short_description = 'Category'

    def status_display(self, obj):
        if obj.agent:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">Assigned</span>'
            )
        return format_html(
            '<span style="background-color: #f59e0b; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">Unassigned</span>'
        )
    status_display.short_description = 'Status'


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'organisation', 'is_active', 'lead_count', 'created_at')
    list_filter = ('is_active', 'organisation', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Agent Information', {
            'fields': ('user', 'organisation', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def user_display(self, obj):
        if obj.user:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:leads_user_change', args=[obj.user.id]),
                obj.user.get_full_name() or obj.user.username
            )
        return '-'
    user_display.short_description = 'User'

    def lead_count(self, obj):
        return obj.leads.count()
    lead_count.short_description = 'Leads'


@admin.register(LeadInteraction)
class LeadInteractionAdmin(admin.ModelAdmin):
    list_display = ('lead', 'agent', 'interaction_type', 'outcome', 'duration_minutes', 'created_at')
    list_filter = ('interaction_type', 'outcome', 'created_at', 'agent')
    search_fields = ('lead__first_name', 'lead__last_name', 'lead__email', 'agent__user__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Interaction Details', {
            'fields': ('lead', 'agent', 'interaction_type', 'outcome')
        }),
        ('Additional Information', {
            'fields': ('notes', 'duration_minutes')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AgentPerformance)
class AgentPerformanceAdmin(admin.ModelAdmin):
    list_display = ('agent', 'date', 'leads_assigned', 'leads_contacted', 'leads_converted', 'conversion_rate', 'contact_rate')
    list_filter = ('date', 'agent', 'agent__organisation')
    search_fields = ('agent__user__username', 'agent__user__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-date',)
    
    fieldsets = (
        ('Performance Metrics', {
            'fields': ('agent', 'date', 'leads_assigned', 'leads_contacted', 'leads_converted')
        }),
        ('Calculated Metrics', {
            'fields': ('total_interactions', 'average_response_time_hours', 'conversion_rate', 'contact_rate')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organisation', 'is_active', 'total_leads', 'conversion_rate', 'created_at')
    list_filter = ('is_active', 'organisation', 'created_at')
    search_fields = ('name', 'organisation__user__username')
    readonly_fields = ('created_at',)
    ordering = ('name',)
    
    fieldsets = (
        ('Source Information', {
            'fields': ('organisation', 'name', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def total_leads(self, obj):
        return obj.total_leads
    total_leads.short_description = 'Total Leads'

    def conversion_rate(self, obj):
        return f"{obj.conversion_rate:.1f}%"
    conversion_rate.short_description = 'Conversion Rate'


# Customize admin site
admin.site.site_header = "LeadFlow Administration"
admin.site.site_title = "LeadFlow Admin"
admin.site.index_title = "Welcome to LeadFlow Administration"

# Customize admin site colors and branding
admin.site.site_url = "/"
