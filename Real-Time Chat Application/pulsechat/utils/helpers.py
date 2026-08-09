import logging
from markupsafe import escape

def setup_logger(name):
    """Creates a pre-configured logger."""
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def sanitize_string(value, max_length):
    """Escapes HTML and truncates to max length."""
    if not value:
        return ""
    return str(escape(value))[:max_length].strip()

def get_deterministic_color(username):
    """
    Generates a deterministic HSL color based on the username string.
    Ensures colors are exactly the same as the JS frontend generator.
    """
    if not username:
        return "hsl(0, 70%, 45%)"
        
    hash_val = 0
    for char in username:
        # Emulate JS string hashing: hash = str.charCodeAt(i) + ((hash << 5) - hash)
        # Python handles large ints natively, we simulate 32-bit overflow by masking
        char_code = ord(char)
        hash_val = (char_code + ((hash_val << 5) - hash_val)) & 0xFFFFFFFF
        
        # Convert to signed 32-bit integer behavior
        if hash_val > 0x7FFFFFFF:
            hash_val -= 0x100000000
            
    h = abs(hash_val) % 360
    return f"hsl({h}, 70%, 45%)"
