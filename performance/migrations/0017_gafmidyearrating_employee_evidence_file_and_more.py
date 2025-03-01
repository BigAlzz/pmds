# Generated by Django 5.0.2 on 2025-02-23 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('performance', '0016_alter_gafmidyearrating_employee_rating_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='gafmidyearrating',
            name='employee_evidence_file',
            field=models.FileField(blank=True, null=True, upload_to='gaf_evidence/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='kramidyearrating',
            name='employee_evidence_file',
            field=models.FileField(blank=True, null=True, upload_to='kra_evidence/%Y/%m/%d/'),
        ),
    ]
