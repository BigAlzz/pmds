# Generated by Django 5.0.2 on 2025-02-24 07:53

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('performance', '0018_alter_improvementplan_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinalReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_date', models.DateField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PENDING_EMPLOYEE_RATING', 'Pending Employee Self-Rating'), ('PENDING_SUPERVISOR_RATING', 'Pending Supervisor Rating'), ('COMPLETED', 'Completed')], default='DRAFT', max_length=30)),
                ('employee_rating_date', models.DateTimeField(blank=True, null=True)),
                ('supervisor_rating_date', models.DateTimeField(blank=True, null=True)),
                ('completion_date', models.DateTimeField(blank=True, null=True)),
                ('employee_overall_comments', models.TextField(blank=True, help_text="Employee's overall comments on the final review")),
                ('supervisor_overall_comments', models.TextField(blank=True, help_text="Supervisor's overall comments on the final review")),
                ('evidence_document', models.FileField(blank=True, null=True, upload_to='final_review_evidence/')),
                ('performance_agreement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='final_reviews', to='performance.performanceagreement')),
            ],
            options={
                'ordering': ['-review_date'],
            },
        ),
        migrations.CreateModel(
            name='GAFFinalRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_rating', models.IntegerField(blank=True, choices=[(4, 'Performance Significantly Above Expectations (4)'), (3, 'Fully Effective Performance (3)'), (2, 'Performance Not Fully Effective (2)'), (1, 'Unacceptable Performance (1)')], null=True)),
                ('employee_comments', models.TextField(blank=True)),
                ('employee_evidence', models.TextField(blank=True, help_text='Description of evidence for the rating')),
                ('employee_evidence_file', models.FileField(blank=True, null=True, upload_to='gaf_evidence/%Y/%m/%d/')),
                ('supervisor_rating', models.IntegerField(blank=True, choices=[(4, 'Performance Significantly Above Expectations (4)'), (3, 'Fully Effective Performance (3)'), (2, 'Performance Not Fully Effective (2)'), (1, 'Unacceptable Performance (1)')], null=True)),
                ('supervisor_comments', models.TextField(blank=True)),
                ('final_review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gaf_ratings', to='performance.finalreview')),
                ('gaf', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='performance.genericassessmentfactor')),
            ],
        ),
        migrations.CreateModel(
            name='KRAFinalRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_rating', models.IntegerField(blank=True, choices=[(4, 'Performance Significantly Above Expectations (4)'), (3, 'Fully Effective Performance (3)'), (2, 'Performance Not Fully Effective (2)'), (1, 'Unacceptable Performance (1)')], null=True)),
                ('employee_comments', models.TextField(blank=True)),
                ('employee_evidence', models.TextField(blank=True, help_text='Description of evidence for the rating')),
                ('employee_evidence_file', models.FileField(blank=True, null=True, upload_to='kra_evidence/%Y/%m/%d/')),
                ('supervisor_rating', models.IntegerField(blank=True, choices=[(4, 'Performance Significantly Above Expectations (4)'), (3, 'Fully Effective Performance (3)'), (2, 'Performance Not Fully Effective (2)'), (1, 'Unacceptable Performance (1)')], null=True)),
                ('supervisor_comments', models.TextField(blank=True)),
                ('final_review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kra_ratings', to='performance.finalreview')),
                ('kra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='performance.keyresponsibilityarea')),
            ],
        ),
    ]
