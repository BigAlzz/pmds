# Generated by Django 5.0.2 on 2025-02-22 18:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('performance', '0004_keyresponsibilityarea_barriers_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenericAssessmentFactor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('factor', models.CharField(choices=[('JOB_KNOWLEDGE', 'Job knowledge'), ('TECHNICAL_SKILLS', 'Technical skills'), ('RESPONSIBILITY', 'Acceptance of responsibility'), ('QUALITY', 'Quality of work'), ('RELIABILITY', 'Reliability'), ('INITIATIVE', 'Initiative'), ('COMMUNICATION', 'Communication'), ('INTERPERSONAL', 'Interpersonal relationships'), ('FLEXIBILITY', 'Flexibility'), ('TEAMWORK', 'Team work'), ('PLANNING', 'Planning and execution'), ('LEADERSHIP', 'Leadership'), ('DELEGATION', 'Delegation and empowerment'), ('FINANCIAL', 'Management of financial resources'), ('HR', 'Management of human resources')], max_length=50)),
                ('is_applicable', models.BooleanField(default=True)),
                ('comments', models.TextField(blank=True)),
                ('performance_agreement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gafs', to='performance.performanceagreement')),
            ],
            options={
                'ordering': ['factor'],
                'unique_together': {('performance_agreement', 'factor')},
            },
        ),
    ]
