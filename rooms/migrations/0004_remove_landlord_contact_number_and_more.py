# Generated by Django 5.1 on 2024-09-26 16:59

import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0003_alter_customuser_last_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='landlord',
            name='contact_number',
        ),
        migrations.RemoveField(
            model_name='leasee',
            name='contact_number',
        ),
        migrations.AddField(
            model_name='customuser',
            name='contact_number',
            field=models.CharField(default=django.utils.timezone.now, help_text='Contact phone number', max_length=15, validators=[django.core.validators.RegexValidator('^\\+?1?\\d{9,15}$', message='Enter a valid phone number')]),
            preserve_default=False,
        ),
    ]
