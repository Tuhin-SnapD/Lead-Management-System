# Generated manually to add timestamp fields

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0010_auto_20201217_2139'),
    ]

    operations = [
        # Add timestamp fields to UserProfile
        migrations.AddField(
            model_name='userprofile',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Add timestamp fields to Category
        migrations.AddField(
            model_name='category',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Add color field to Category
        migrations.AddField(
            model_name='category',
            name='color',
            field=models.CharField(default='#3B82F6', help_text='Hex color code for category display', max_length=7),
        ),
        
        # Add timestamp fields to Agent
        migrations.AddField(
            model_name='agent',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='agent',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Add is_active field to Agent
        migrations.AddField(
            model_name='agent',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        
        # Add new fields to Lead model
        migrations.AddField(
            model_name='lead',
            name='source',
            field=models.CharField(blank=True, help_text='Source of the lead (e.g., website, referral, cold call)', max_length=100),
        ),
        migrations.AddField(
            model_name='lead',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='last_contacted',
            field=models.DateTimeField(blank=True, help_text='Date when the lead was last contacted', null=True),
        ),
        
        # Add indexes for better performance
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['organisation', 'agent'], name='leads_lead_organis_8b8c8c_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['organisation', 'category'], name='leads_lead_organis_9c9d9d_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['date_added'], name='leads_lead_date_ad_1a2b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['last_contacted'], name='leads_lead_last_co_4d5e6f_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['email'], name='leads_lead_email_7g8h9i_idx'),
        ),
        
        # Add indexes for User model
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_organisor', 'is_agent'], name='leads_user_is_orga_j0k1l2_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['username'], name='leads_user_usernam_m3n4o5_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='leads_user_email_p6q7r8_idx'),
        ),
        
        # Add indexes for Category model
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['organisation', 'name'], name='leads_catego_organis_s9t0u1_idx'),
        ),
        
        # Add indexes for Agent model
        migrations.AddIndex(
            model_name='agent',
            index=models.Index(fields=['organisation', 'is_active'], name='leads_agent_organis_v2w3x4_idx'),
        ),
        migrations.AddIndex(
            model_name='agent',
            index=models.Index(fields=['user'], name='leads_agent_user_id_y5z6a7_idx'),
        ),
    ] 