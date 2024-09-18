from django.core.exceptions import ValidationError
from profanity_check import predict
import re
import defusedxml.ElementTree as ET
import guardrails as gr
# from guardrails.validators import Validator

def validate_no_contact_info(content, user):

    # Check for inappropriate content using profanity-check
    if predict([content])[0] == 1:
        raise ValidationError("Content contains inappropriate language.")

    if user.is_superuser:# or user.is_premium:
        return  # Skip validation for premium or superusers

    # Regular expressions for phone numbers, emails, and URLs
    phone_regex = re.compile(r'(\+?\d[\d -]{8,}\d)')
    email_regex = re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.IGNORECASE)
    url_regex = re.compile(r'https?://(?:www\.)?(?:[a-zA-Z0-9\-]+\s*\.\s*)+[a-zA-Z]{2,}(?:[^\s]*)')
    url_regex2 = re.compile(r'www\.(?:[a-zA-Z0-9\-]+\s*\.\s*)+[a-zA-Z]{2,}(?:[^\s]*)')
    
    # Check for phone numbers, emails, and URLs
    if phone_regex.search(content):
        raise ValidationError("Content cannot contain phone numbers.")
    if email_regex.search(content):
        raise ValidationError("Content cannot contain email addresses.")
    if url_regex.search(content):
        raise ValidationError("Content cannot contain website URLs.")
    if url_regex2.search(content):
        raise ValidationError("Content cannot contain website URLs.")
    

def validate_for_malicious_content(content):
    # Basic SQL Injection patterns
    sql_injection_patterns = [
        re.compile(r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b)", re.IGNORECASE),
        re.compile(r"(--|#|\/\*|\*\/)", re.IGNORECASE)
    ]

    # Basic XSS patterns
    xss_patterns = [
        re.compile(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', re.IGNORECASE),
        re.compile(r'[\w]+=\"javascript:', re.IGNORECASE)
    ]
    
    # Validate for SQL Injection
    for pattern in sql_injection_patterns:
        if pattern.search(content):
            raise ValidationError("Content contains SQL injection patterns.")
    
    # Validate for XSS
    for pattern in xss_patterns:
        if pattern.search(content):
            raise ValidationError("Content contains cross-site scripting (XSS) patterns.")

    # Validate for malicious XML
    # try:
    #     ET.fromstring(content)
    # except ET.ParseError:
    #     raise ValidationError("Invalid XML content detected.")


# Custom validator for inappropriate content using Guardrails
def validate_inappropriate_content(content):
    if gr.inappropriate_language(content):
        raise ValidationError("Content contains inappropriate language.")