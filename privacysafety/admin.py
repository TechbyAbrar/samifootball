from django.contrib import admin
from .models import PrivacyPolicy, TrustSafety, TermsConditions, ContactForm
# Register your models here.

@admin.register(PrivacyPolicy)
class PrivacyAndPolicyAdmin(admin.ModelAdmin):
    list_display = ['description']

@admin.register(TrustSafety)
class TrustAndSafetyAdmin(admin.ModelAdmin):
    list_display = ['description']

@admin.register(TermsConditions)
class TermsAndConditionAdmin(admin.ModelAdmin):
    list_display = ['description']
    
@admin.register(ContactForm)
class ContactFormAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone_number', 'created_at']
    search_fields = ['name', 'email']
    list_filter = ['created_at']