# Generated by Django 5.1 on 2024-10-24 11:21

import datetime
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0004_deposit_landlord_alter_deposit_leasee_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='district',
            field=models.CharField(default=datetime.datetime(2024, 10, 24, 11, 21, 8, 158004, tzinfo=datetime.timezone.utc), help_text='District name', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='room',
            name='province',
            field=models.CharField(choices=[('Province 1', 'Province 1'), ('Province 2', 'Province 2'), ('Bagmati', 'Bagmati'), ('Gandaki', 'Gandaki'), ('Lumbini', 'Lumbini'), ('Karnali', 'Karnali'), ('Sudurpashchim', 'Sudurpashchim')], default=django.utils.timezone.now, help_text='Select a province', max_length=255),
            preserve_default=False,
        ),
    ]