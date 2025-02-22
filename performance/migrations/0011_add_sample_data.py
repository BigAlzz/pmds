from django.db import migrations
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from datetime import timedelta

def create_sample_data(apps, schema_editor):
    CustomUser = apps.get_model('performance', 'CustomUser')
    PerformanceAgreement = apps.get_model('performance', 'PerformanceAgreement')
    KeyResponsibilityArea = apps.get_model('performance', 'KeyResponsibilityArea')
    GenericAssessmentFactor = apps.get_model('performance', 'GenericAssessmentFactor')
    SalaryLevel = apps.get_model('performance', 'SalaryLevel')

    # Get salary levels
    level_16 = SalaryLevel.objects.get(level='16')  # DG
    level_15 = SalaryLevel.objects.get(level='15')  # DDG
    level_13 = SalaryLevel.objects.get(level='13')  # Director
    level_11 = SalaryLevel.objects.get(level='11')  # Deputy Director
    level_8 = SalaryLevel.objects.get(level='8')    # Junior Manager
    level_7 = SalaryLevel.objects.get(level='7')    # Senior Admin Officer

    # Create DG (Approver)
    dg = CustomUser.objects.create(
        username='dg.smith',
        password=make_password('password123'),
        first_name='James',
        last_name='Smith',
        email='dg.smith@department.gov.za',
        employee_id='EMP001',
        persal_number='10023456',
        role='APPROVER',
        department='Office of the Director-General',
        job_title='Director-General',
        job_purpose='Provide strategic leadership and oversight for the department',
        school_directorate='Director-General Office',
        date_of_appointment=timezone.now().date() - timedelta(days=365*5),
        salary_level=level_16
    )

    # Create DDG (Approver)
    ddg = CustomUser.objects.create(
        username='ddg.jones',
        password=make_password('password123'),
        first_name='Sarah',
        last_name='Jones',
        email='ddg.jones@department.gov.za',
        employee_id='EMP002',
        persal_number='10034567',
        role='APPROVER',
        department='Corporate Services',
        job_title='Deputy Director-General: Corporate Services',
        job_purpose='Lead and manage corporate services functions',
        school_directorate='Corporate Services Branch',
        date_of_appointment=timezone.now().date() - timedelta(days=365*4),
        salary_level=level_15,
        manager=dg
    )

    # Create HR Director
    hr_director = CustomUser.objects.create(
        username='hr.director',
        password=make_password('password123'),
        first_name='Michael',
        last_name='Brown',
        email='m.brown@department.gov.za',
        employee_id='EMP003',
        persal_number='10045678',
        role='HR',
        department='Human Resources',
        job_title='Director: Human Resources',
        job_purpose='Direct and oversee HR operations and strategy',
        school_directorate='HR Directorate',
        date_of_appointment=timezone.now().date() - timedelta(days=365*3),
        salary_level=level_13,
        manager=ddg
    )

    # Create Manager
    manager = CustomUser.objects.create(
        username='p.wilson',
        password=make_password('password123'),
        first_name='Patricia',
        last_name='Wilson',
        email='p.wilson@department.gov.za',
        employee_id='EMP004',
        persal_number='10056789',
        role='MANAGER',
        department='Finance',
        job_title='Deputy Director: Financial Management',
        job_purpose='Manage financial operations and reporting',
        school_directorate='Finance Directorate',
        date_of_appointment=timezone.now().date() - timedelta(days=365*2),
        salary_level=level_11,
        manager=ddg
    )

    # Create Employees
    employee1 = CustomUser.objects.create(
        username='j.doe',
        password=make_password('password123'),
        first_name='John',
        last_name='Doe',
        email='j.doe@department.gov.za',
        employee_id='EMP005',
        persal_number='10067890',
        role='EMPLOYEE',
        department='Finance',
        job_title='Senior Financial Officer',
        job_purpose='Process and manage financial transactions',
        school_directorate='Finance Directorate',
        date_of_appointment=timezone.now().date() - timedelta(days=365),
        salary_level=level_8,
        manager=manager
    )

    employee2 = CustomUser.objects.create(
        username='a.smith',
        password=make_password('password123'),
        first_name='Alice',
        last_name='Smith',
        email='a.smith@department.gov.za',
        employee_id='EMP006',
        persal_number='10078901',
        role='EMPLOYEE',
        department='Finance',
        job_title='Administrative Officer',
        job_purpose='Provide administrative support to the finance team',
        school_directorate='Finance Directorate',
        date_of_appointment=timezone.now().date() - timedelta(days=180),
        salary_level=level_7,
        manager=manager
    )

    # Create Performance Agreements
    # Agreement for Manager
    manager_agreement = PerformanceAgreement.objects.create(
        employee=manager,
        supervisor=ddg,
        approver=dg,
        pmds_administrator=hr_director,
        agreement_date=timezone.now().date() - timedelta(days=60),
        plan_start_date=timezone.now().date() - timedelta(days=30),
        plan_end_date=timezone.now().date() + timedelta(days=335),
        midyear_review_date=timezone.now().date() + timedelta(days=152),
        final_assessment_date=timezone.now().date() + timedelta(days=335),
        status='PENDING_APPROVER_REVIEW',
        employee_submitted_date=timezone.now() - timedelta(days=5),
        supervisor_reviewed_date=timezone.now() - timedelta(days=2),
        employee_comments='I have set ambitious but achievable targets.',
        supervisor_comments='The KRAs are well-defined and aligned with departmental goals.'
    )

    # KRAs for Manager
    KeyResponsibilityArea.objects.create(
        performance_agreement=manager_agreement,
        description='Financial Management and Reporting',
        performance_objective='Ensure accurate and timely financial reporting',
        weighting=30.00,
        measurement='Monthly reports submitted by due date, Accuracy rate > 98%',
        target_date=timezone.now().date() + timedelta(days=335),
        tools='Financial Management System, Excel',
        barriers='System downtime, Late submissions from other departments',
        evidence_examples='Monthly reports, Audit findings'
    )

    KeyResponsibilityArea.objects.create(
        performance_agreement=manager_agreement,
        description='Budget Management',
        performance_objective='Effective budget control and monitoring',
        weighting=25.00,
        measurement='Variance < 5%, No unauthorized expenditure',
        target_date=timezone.now().date() + timedelta(days=335),
        tools='Budget management system, Financial policies',
        barriers='Unexpected expenses, Policy changes',
        evidence_examples='Budget reports, Variance analysis'
    )

    # Agreement for Employee 1
    emp1_agreement = PerformanceAgreement.objects.create(
        employee=employee1,
        supervisor=manager,
        approver=ddg,
        pmds_administrator=hr_director,
        agreement_date=timezone.now().date() - timedelta(days=45),
        plan_start_date=timezone.now().date() - timedelta(days=30),
        plan_end_date=timezone.now().date() + timedelta(days=335),
        midyear_review_date=timezone.now().date() + timedelta(days=152),
        final_assessment_date=timezone.now().date() + timedelta(days=335),
        status='PENDING_SUPERVISOR_RATING',
        employee_submitted_date=timezone.now() - timedelta(days=3),
        employee_comments='I have included all my key responsibilities and targets.'
    )

    # KRAs for Employee 1
    KeyResponsibilityArea.objects.create(
        performance_agreement=emp1_agreement,
        description='Transaction Processing',
        performance_objective='Efficient and accurate processing of financial transactions',
        weighting=40.00,
        measurement='Processing time < 24 hours, Accuracy rate > 95%',
        target_date=timezone.now().date() + timedelta(days=335),
        tools='Financial System, Calculator',
        barriers='System issues, Incomplete documentation',
        evidence_examples='Transaction logs, Error reports'
    )

    # Agreement for Employee 2
    emp2_agreement = PerformanceAgreement.objects.create(
        employee=employee2,
        supervisor=manager,
        approver=ddg,
        pmds_administrator=hr_director,
        agreement_date=timezone.now().date() - timedelta(days=30),
        plan_start_date=timezone.now().date() - timedelta(days=30),
        plan_end_date=timezone.now().date() + timedelta(days=335),
        midyear_review_date=timezone.now().date() + timedelta(days=152),
        final_assessment_date=timezone.now().date() + timedelta(days=335),
        status='DRAFT'
    )

    # KRAs for Employee 2
    KeyResponsibilityArea.objects.create(
        performance_agreement=emp2_agreement,
        description='Administrative Support',
        performance_objective='Provide efficient administrative support',
        weighting=35.00,
        measurement='Task completion rate > 90%, Customer satisfaction > 85%',
        target_date=timezone.now().date() + timedelta(days=335),
        tools='MS Office, Filing System',
        barriers='High workload, Multiple urgent requests',
        evidence_examples='Task completion records, Feedback forms'
    )

    # Add Generic Assessment Factors for each agreement
    for agreement in [manager_agreement, emp1_agreement, emp2_agreement]:
        for gaf in GenericAssessmentFactor.GAF_CHOICES:
            GenericAssessmentFactor.objects.create(
                performance_agreement=agreement,
                factor=gaf[0],
                is_applicable=True,
                comments=f'Standard assessment for {gaf[1]}'
            )

def remove_sample_data(apps, schema_editor):
    CustomUser = apps.get_model('performance', 'CustomUser')
    CustomUser.objects.filter(username__in=[
        'dg.smith', 'ddg.jones', 'hr.director', 'p.wilson', 'j.doe', 'a.smith'
    ]).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('performance', '0010_update_salary_level_structure'),
    ]

    operations = [
        migrations.RunPython(create_sample_data, remove_sample_data),
    ] 