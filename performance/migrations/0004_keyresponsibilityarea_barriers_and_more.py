# Generated by Django 5.0.2 on 2025-02-22 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('performance', '0003_remove_performanceagreement_gafs_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='keyresponsibilityarea',
            name='barriers',
            field=models.TextField(blank=True, help_text='Potential barriers or challenges'),
        ),
        migrations.AddField(
            model_name='keyresponsibilityarea',
            name='evidence_examples',
            field=models.TextField(blank=True, help_text='Examples of evidence that can be provided'),
        ),
        migrations.AddField(
            model_name='keyresponsibilityarea',
            name='performance_objective',
            field=models.TextField(blank=True, help_text='Performance Objective/Output', null=True),
        ),
        migrations.AddField(
            model_name='keyresponsibilityarea',
            name='target_date',
            field=models.DateField(blank=True, help_text='Target date for completion', null=True),
        ),
        migrations.AddField(
            model_name='keyresponsibilityarea',
            name='tools',
            field=models.TextField(blank=True, help_text='Tools required for this KRA'),
        ),
    ]
