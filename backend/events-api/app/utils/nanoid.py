"""
NanoID utility functions
"""
from nanoid import generate

def generate_id(size: int = 12) -> str:
    """
    Generate a NanoID with specified size
    
    Args:
        size: Length of the ID (default: 12)
        
    Returns:
        str: Generated NanoID
    """
    return generate(size=size)

def generate_user_id() -> str:
    """Generate a user ID"""
    return generate_id(12)

def generate_event_id() -> str:
    """Generate an event ID"""
    return generate_id(12)

def generate_agenda_id() -> str:
    """Generate an agenda ID"""
    return generate_id(12)

def generate_agenda_item_id() -> str:
    """Generate an agenda item ID"""
    return generate_id(12)