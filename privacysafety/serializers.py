from rest_framework import serializers
from .models import PrivacyPolicy, TrustSafety, TermsConditions, ContactForm

class BaseContentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'description', 'last_updated']
        read_only_fields = ['id', 'last_updated']

class PrivacyPolicySerializer(BaseContentSerializer):
    class Meta(BaseContentSerializer.Meta):
        model = PrivacyPolicy

class TrustSafetySerializer(BaseContentSerializer):
    class Meta(BaseContentSerializer.Meta):
        model = TrustSafety

class TermsConditionsSerializer(BaseContentSerializer):
    class Meta(BaseContentSerializer.Meta):
        model = TermsConditions 


# Contact Form Serializer
class ContactFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactForm
        fields = ['id', 'name', 'email', 'phone_number', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
