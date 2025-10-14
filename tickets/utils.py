# tickets/utils.py
import uuid

def generate_ticket_id() -> str:
    return uuid.uuid4().hex[:10].upper()

def generate_unique_purchase_id() -> str:
    return uuid.uuid4().hex[:12].upper()

def validate_quantity(quantity: int, available: int) -> None:
    """Validate ticket purchase quantity."""
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")
    if quantity > available:
        raise ValueError(f"Only {available} tickets available.")


