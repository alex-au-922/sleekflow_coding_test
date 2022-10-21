import string
import random

def random_string(length: int = 10) -> str:
    """Generate random string"""

    chars: str = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))
