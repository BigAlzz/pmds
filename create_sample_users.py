import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'performance_management_system.settings')
django.setup()

from performance.models import CustomUser, SalaryLevel

def create_sample_users():
    # Get salary levels
    dg_level = SalaryLevel.objects.get(level='16')
    ddg_level = SalaryLevel.objects.get(level='15')
    director_level = SalaryLevel.objects.get(level='13')
    manager_level = SalaryLevel.objects.get(level='11')
    employee_level = SalaryLevel.objects.get(level='8')
    
    # Create Director-General (Approver)
    dg = CustomUser.objects.create_user(
        username='dg',
        password='dg123',
        first_name='James',
        last_name='Smith',
        email='dg@gcra.gauteng.gov.za',
        employee_id='EMP001',
        persal_number='PER001',
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
    ddg = CustomUser.objects.create_user(
        username='ddg',
        password='ddg123',
        first_name='Sarah',
        last_name='Jones',
        email='ddg@gcra.gauteng.gov.za',
        employee_id='EMP002',
        persal_number='PER002',
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
    hr_director = CustomUser.objects.create_user(
        username='hr',
        password='hr123',
        first_name='Michael',
        last_name='Brown',
        email='hr@gcra.gauteng.gov.za',
        employee_id='EMP003',
        persal_number='PER003',
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
    manager = CustomUser.objects.create_user(
        username='manager',
        password='manager123',
        first_name='Patricia',
        last_name='Wilson',
        email='manager@gcra.gauteng.gov.za',
        employee_id='EMP004',
        persal_number='PER004',
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
    employee1 = CustomUser.objects.create_user(
        username='john',
        password='john123',
        first_name='John',
        last_name='Doe',
        email='john@gcra.gauteng.gov.za',
        employee_id='EMP005',
        persal_number='PER005',
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
    
    employee2 = CustomUser.objects.create_user(
        username='alice',
        password='alice123',
        first_name='Alice',
        last_name='Smith',
        email='alice@gcra.gauteng.gov.za',
        employee_id='EMP006',
        persal_number='PER006',
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
    
    print("Sample users created successfully!")

if __name__ == '__main__':
    create_sample_users() 