# Generated manually to add missing fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0011_add_timestamp_fields'),
    ]

    operations = [
        # Add color field to Category if it doesn't exist
        migrations.AddField(
            model_name='category',
            name='color',
            field=models.CharField(default='#3B82F6', help_text='Hex color code for category display', max_length=7),
        ),
    ] 