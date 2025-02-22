# Generated by Django 4.2.7 on 2025-02-22 16:11

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('employee_id', models.CharField(max_length=20, unique=True)),
                ('role', models.CharField(choices=[('EMPLOYEE', 'Employee'), ('MANAGER', 'Manager'), ('HR', 'HR')], default='EMPLOYEE', max_length=10)),
                ('department', models.CharField(max_length=100)),
                ('job_title', models.CharField(max_length=100)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='PersonalDevelopmentPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('competency_gap', models.TextField()),
                ('development_activities', models.TextField()),
                ('timeline', models.TextField()),
                ('expected_outcome', models.TextField()),
                ('progress', models.IntegerField(default=0, help_text='Progress percentage')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PerformanceAgreement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_date', models.DateField(default=django.utils.timezone.now)),
                ('kras', models.TextField(help_text='Key Result Areas')),
                ('gafs', models.TextField(help_text='General Areas for Focus')),
                ('objectives', models.TextField()),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PENDING_APPROVAL', 'Pending Approval'), ('APPROVED', 'Approved'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed')], default='DRAFT', max_length=20)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MidYearReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('self_rating', models.TextField()),
                ('supervisor_rating', models.TextField()),
                ('final_rating', models.CharField(choices=[('EXCEEDS', 'Exceeds Expectations'), ('MEETS', 'Meets Expectations'), ('NEEDS_IMPROVEMENT', 'Needs Improvement'), ('UNSATISFACTORY', 'Unsatisfactory')], max_length=20)),
                ('comments', models.TextField()),
                ('review_date', models.DateField(default=django.utils.timezone.now)),
                ('performance_agreement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='performance.performanceagreement')),
            ],
        ),
        migrations.CreateModel(
            name='ImprovementPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area_for_development', models.TextField()),
                ('interventions', models.TextField()),
                ('timeline', models.TextField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed')], default='PENDING', max_length=20)),
                ('approval_date', models.DateField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_plans', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedback', models.TextField()),
                ('anonymous', models.BooleanField(default=False)),
                ('submitted_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model', models.CharField(max_length=50)),
                ('instance_id', models.IntegerField()),
                ('action', models.CharField(choices=[('CREATE', 'Create'), ('UPDATE', 'Update'), ('DELETE', 'Delete')], max_length=20)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('changes', models.TextField(help_text='JSON representation of changes')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
