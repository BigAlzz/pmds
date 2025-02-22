# Generated by Django 5.0.2 on 2025-02-22 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('performance', '0007_populate_salary_levels'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='salarylevel',
            options={'ordering': ['numeric_level']},
        ),
        migrations.AddField(
            model_name='salarylevel',
            name='numeric_level',
            field=models.IntegerField(default=1, editable=False),
        ),
    ]
