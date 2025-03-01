"""
Utility functions for the performance management system.
"""
from .models import AuditTrail

def log_audit_event(user, action, request=None, obj=None, details=""):
    """
    Log an audit event for tracking purposes.
    
    Args:
        user: The user performing the action
        action: The action being performed (use AuditTrail.ACTION_* constants)
        request: The HTTP request (optional, used to get IP and user agent)
        obj: The object being affected (optional)
        details: Additional details about the action (optional)
    
    Returns:
        The created AuditTrail instance
    """
    # Extract IP and user agent from request if available
    ip_address = None
    user_agent = ""
    if request and hasattr(request, 'META'):
        ip_address = request.META.get('REMOTE_ADDR', None)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Extract object information if available
    content_type = ""
    object_id = None
    object_repr = ""
    if obj:
        content_type = obj.__class__.__name__
        if hasattr(obj, 'pk'):
            object_id = obj.pk
        object_repr = str(obj)
    
    # Create the audit trail entry
    audit_trail = AuditTrail.objects.create(
        user=user,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        content_type=content_type,
        object_id=object_id,
        object_repr=object_repr,
        details=details
    )
    
    return audit_trail 