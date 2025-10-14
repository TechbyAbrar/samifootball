import random
import logging
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail, BadHeaderError
from django.core.exceptions import ImproperlyConfigured
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

def generate_otp(length=6) -> str:
    """Generate a numeric OTP of specified length."""
    range_start = 10**(length-1)
    range_end = (10**length) - 1
    return str(random.randint(range_start, range_end))

def get_otp_expiry(minutes=30):
    """Return expiry timestamp for OTP."""
    return timezone.now() + timedelta(minutes=minutes)

def send_otp_email(recipient_email: str, otp: str) -> None:
    """Send an OTP to the user's email."""
    from_email = getattr(settings, 'EMAIL_HOST_USER', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if not from_email:
        raise ImproperlyConfigured("Sender email not configured. Set EMAIL_HOST_USER or DEFAULT_FROM_EMAIL in settings.")

    subject = "Verify Your Email"
    message = f"Your One-Time Password (OTP) is: {otp}"

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"OTP email sent to {recipient_email}")
    except BadHeaderError:
        logger.error("Invalid header found while sending email.")
    except Exception as e:
        logger.exception(f"Error sending OTP email to {recipient_email}: {e}")

def generate_tokens_for_user(user):
    """Generates access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

from django.core.exceptions import ValidationError
from PIL import Image

def validate_image(image):
    """Validate image size and format."""
    if image:
        max_size = 5 * 1024 * 1024  # 5MB
        allowed_formats = ['JPEG', 'PNG', 'GIF']
        if image.size > max_size:
            raise ValidationError('Image file too large (max 5MB).')
        img = Image.open(image)
        if img.format not in allowed_formats:
            raise ValidationError(f'Unsupported image format: {img.format}. Allowed formats: {allowed_formats}')
        