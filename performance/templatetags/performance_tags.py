from django import template
from django.utils import formats
from django.utils.safestring import mark_safe
import datetime
from performance.models import GenericAssessmentFactor

register = template.Library()

@register.filter
def get_item(queryset, index):
    """Get an item from a queryset by index"""
    try:
        return queryset[index]
    except (IndexError, TypeError):
        return None

@register.filter
def get_display_fields(obj):
    """
    Returns a list of formatted field values for display in templates.
    """
    if not hasattr(obj, 'display_fields'):
        return []

    result = []
    for field_name in obj.display_fields:
        value = getattr(obj, field_name)
        field_type = type(value).__name__

        field_info = {
            'value': value,
            'is_status': field_name == 'status',
            'is_progress': field_name == 'progress',
            'is_date': field_type == 'date' or field_type == 'datetime'
        }
        result.append(field_info)

    return result

@register.filter
def get_attribute(obj, attr_name):
    """
    Returns the value of an attribute from an object.
    Handles special cases like dates, status, progress, and foreign keys.
    """
    value = getattr(obj, attr_name, '')
    
    # Handle special cases
    if attr_name == 'status':
        return mark_safe(f'<span class="badge bg-{value.lower()}">{value}</span>')
    elif attr_name == 'progress':
        return mark_safe(
            f'<div class="progress">'
            f'<div class="progress-bar" role="progressbar" '
            f'style="width: {value}%" '
            f'aria-valuenow="{value}" aria-valuemin="0" aria-valuemax="100">'
            f'{value}%</div></div>'
        )
    elif isinstance(value, (datetime.date, datetime.datetime)):
        return formats.date_format(value, "M d, Y")
    elif attr_name == 'employee' and hasattr(value, 'get_full_name'):
        # Handle employee foreign key
        return value.get_full_name()
    
    return value

@register.filter
def add_class(field, css_class):
    """
    Adds a CSS class to a form field.
    """
    return field.as_widget(attrs={'class': css_class})

@register.filter
def get_model_name(obj):
    """
    Returns the model name of an object.
    """
    return obj._meta.model_name

@register.filter
def get_verbose_name(obj):
    """
    Returns the verbose name of a model.
    """
    return obj._meta.verbose_name

@register.filter
def get_verbose_name_plural(obj):
    """
    Returns the plural verbose name of a model.
    """
    return obj._meta.verbose_name_plural

@register.filter
def get_field_type(field):
    """
    Returns the field type for a form field.
    """
    return field.field.widget.__class__.__name__

@register.filter
def get_gaf_display(value):
    """Get the display value for a GAF choice"""
    choices_dict = dict(GenericAssessmentFactor.GAF_CHOICES)
    return choices_dict.get(value, value)

@register.filter
def status_badge(status):
    """Returns a styled badge for the given status"""
    status_colors = {
        'DRAFT': 'secondary',
        'PENDING_EMPLOYEE_RATING': 'info',
        'PENDING_SUPERVISOR_RATING': 'primary',
        'PENDING_AGREEMENT': 'warning',
        'PENDING_ADMIN_APPROVAL': 'info',
        'COMPLETED': 'success',
        'REJECTED': 'danger'
    }
    
    color = status_colors.get(status, 'secondary')
    display = status.replace('_', ' ').title()
    
    return mark_safe(
        f'<span class="badge bg-{color} status-badge">'
        f'<i class="bi {get_status_icon(status)} me-1"></i>'
        f'{display}</span>'
    )

def get_status_icon(status):
    """Returns the appropriate Bootstrap icon for the status"""
    status_icons = {
        'DRAFT': 'bi-file-earmark',
        'PENDING_EMPLOYEE_RATING': 'bi-person-check',
        'PENDING_SUPERVISOR_RATING': 'bi-people',
        'PENDING_AGREEMENT': 'bi-chat-dots',
        'PENDING_ADMIN_APPROVAL': 'bi-shield-check',
        'COMPLETED': 'bi-check-circle',
        'REJECTED': 'bi-x-circle'
    }
    return status_icons.get(status, 'bi-question-circle')

@register.filter
def can_delete_agreement(agreement, user):
    """Template filter to check if a user can delete an agreement"""
    return agreement.can_delete(user)

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divides the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def sum_attr(queryset, attr_name):
    """Sums up the values of a specific attribute across all objects in a queryset"""
    total = 0
    for obj in queryset:
        try:
            # Handle nested attributes with dot notation
            if '.' in attr_name:
                parts = attr_name.split('.')
                value = obj
                for part in parts:
                    value = getattr(value, part)
            else:
                value = getattr(obj, attr_name)
            total += float(value)
        except (AttributeError, ValueError, TypeError):
            pass
    return total
