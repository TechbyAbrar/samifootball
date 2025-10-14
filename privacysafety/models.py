from django.db import models

class BaseContent(models.Model):
    description = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.description[:50]  # Return first 50 characters of description

class PrivacyPolicy(BaseContent):
    pass

class TrustSafety(BaseContent):
    pass

class TermsConditions(BaseContent):
    pass



class ContactForm(models.Model):
    name = models.CharField(max_length=100, help_text="Abrar Fahim")
    email = models.EmailField(help_text="abc@gmail.com")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    message = models.TextField(help_text="Your message here")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact from {self.email} at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    