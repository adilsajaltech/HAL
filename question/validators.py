import re
from django.core.exceptions import ValidationError

def validate_no_contact_info(content, user):
    """
    Validates that the content does not contain phone numbers, emails, or URLs.
    Excludes validation for admin or premium users.
    """
    if user.is_superuser or user.is_premium:  # Assuming `is_premium` is a field for premium users
        return  # Skip validation for admin and premium users

    phone_regex = re.compile(r'(\+?\d[\d -]{8,}\d)')
    email_regex = re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.IGNORECASE)
    url_regex = re.compile(r'(https?://[^\s]+)')
    
    if phone_regex.search(content):
        raise ValidationError("Content cannot contain phone numbers.")
    if email_regex.search(content):
        raise ValidationError("Content cannot contain email addresses.")
    if url_regex.search(content):
        raise ValidationError("Content cannot contain website URLs.")
