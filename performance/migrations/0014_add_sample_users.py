from django.db import migrations
from django.utils import timezone
from django.contrib.auth.hashers import make_password

def create_sample_users(apps, schema_editor):
    CustomUser = apps.get_model('performance', 'CustomUser')
    SalaryLevel = apps.get_model('performance', 'SalaryLevel')
    
    # Get salary levels
    dg_level = SalaryLevel.objects.get(level='16')
    ddg_level = SalaryLevel.objects.get(level='15')
    director_level = SalaryLevel.objects.get(level='13')
    manager_level = SalaryLevel.objects.get(level='11')
    employee_level = SalaryLevel.objects.get(level='8')
    
    # Create Director-General (Approver)
    dg = CustomUser.objects.create(
        username='dg',
        password=make_password('dg123'),
        first_name='James',
        last_name='Smith',
        email='dg@gcra.gauteng.gov.za',
        employee_id='EMP101',
        persal_number='PER101',
        role='APPROVER',
        department='Office of the DG',
        job_title='Director-General',
        job_purpose='Head of Department',
        school_directorate='Executive Office',
        date_of_appointment=timezone.now().date(),
        salary_level=dg_level,
        is_staff=True
    )
    
    # Create Deputy Director-General (Approver)
    ddg = CustomUser.objects.create(
        username='ddg',
        password=make_password('ddg123'),
        first_name='Sarah',
        last_name='Jones',
        email='ddg@gcra.gauteng.gov.za',
        employee_id='EMP102',
        persal_number='PER102',
        role='APPROVER',
        department='Corporate Services',
        job_title='Deputy Director-General',
        job_purpose='Head of Corporate Services',
        school_directorate='Corporate Services',
        date_of_appointment=timezone.now().date(),
        salary_level=ddg_level,
        manager=dg,
        is_staff=True
    )
    
    # Create HR Director
    hr_director = CustomUser.objects.create(
        username='hr',
        password=make_password('hr123'),
        first_name='Michael',
        last_name='Brown',
        email='hr@gcra.gauteng.gov.za',
        employee_id='EMP103',
        persal_number='PER103',
        role='HR',
        department='Human Resources',
        job_title='Director: HR',
        job_purpose='Human Resources Management',
        school_directorate='Corporate Services',
        date_of_appointment=timezone.now().date(),
        salary_level=director_level,
        manager=ddg,
        is_staff=True
    )
    
    # Create Manager
    manager = CustomUser.objects.create(
        username='manager',
        password=make_password('manager123'),
        first_name='Patricia',
        last_name='Wilson',
        email='manager@gcra.gauteng.gov.za',
        employee_id='EMP104',
        persal_number='PER104',
        role='MANAGER',
        department='Finance',
        job_title='Deputy Director: Finance',
        job_purpose='Financial Management',
        school_directorate='Corporate Services',
        date_of_appointment=timezone.now().date(),
        salary_level=manager_level,
        manager=ddg,
        is_staff=True
    )
    
    # Create Employees
    employee1 = CustomUser.objects.create(
        username='john',
        password=make_password('john123'),
        first_name='John',
        last_name='Doe',
        email='john@gcra.gauteng.gov.za',
        employee_id='EMP105',
        persal_number='PER105',
        role='EMPLOYEE',
        department='Finance',
        job_title='Assistant Director: Finance',
        job_purpose='Financial Administration',
        school_directorate='Corporate Services',
        date_of_appointment=timezone.now().date(),
        salary_level=employee_level,
        manager=manager,
        is_staff=True
    )
    
    employee2 = CustomUser.objects.create(
        username='alice',
        password=make_password('alice123'),
        first_name='Alice',
        last_name='Smith',
        email='alice@gcra.gauteng.gov.za',
        employee_id='EMP106',
        persal_number='PER106',
        role='EMPLOYEE',
        department='Finance',
        job_title='State Accountant',
        job_purpose='Financial Accounting',
        school_directorate='Corporate Services',
        date_of_appointment=timezone.now().date(),
        salary_level=employee_level,
        manager=manager,
        is_staff=True
    )

def remove_sample_users(apps, schema_editor):
    CustomUser = apps.get_model('performance', 'CustomUser')
    CustomUser.objects.filter(username__in=['dg', 'ddg', 'hr', 'manager', 'john', 'alice']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('performance', '0013_fix_sample_data'),
    ]

    operations = [
        migrations.RunPython(create_sample_users, remove_sample_users),
    ] 