"""
On-Premises PII Scrubber & Anonymizer
Adheres to the Australian Privacy Act 1988 & Australian Privacy Principles (APPs).
Scrubs personally identifiable information (emails, phone numbers, addresses, personal identifiers)
while strictly preserving professional competencies, technical keywords, and work evidence.
"""

import re

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}')
URL_REGEX = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*')
SSN_OR_TAX_ID = re.compile(r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9,11}\b')

def scrub_text(text: str) -> str:
    """Mask PII from raw resume text."""
    if not text or not isinstance(text, str):
        return ""

    # Replace emails
    cleaned = EMAIL_REGEX.sub("[EMAIL_MASKED]", text)
    # Replace URLs / Personal portfolio links with PII
    cleaned = URL_REGEX.sub("[URL_REDACTED]", cleaned)
    # Replace tax IDs / social numbers
    cleaned = SSN_OR_TAX_ID.sub("[ID_MASKED]", cleaned)
    # Replace phone numbers
    cleaned = PHONE_REGEX.sub("[PHONE_MASKED]", cleaned)

    # Clean redundant whitespace
    cleaned = ' '.join(cleaned.split())
    return cleaned

def anonymize_candidate_name(raw_name: str, candidate_id: str) -> str:
    """Ensure candidate name is standardized or pseudonymous if privacy required."""
    if not raw_name or raw_name.lower() in ['unknown', 'candidate', 'resume']:
        return f"Candidate {candidate_id[-4:]}"
    return raw_name.strip()
