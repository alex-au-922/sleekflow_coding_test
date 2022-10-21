import re 

def is_email_format(email: str) -> bool:
    """Check if email is valid"""

    pattern = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    return re.fullmatch(pattern, email) is not None