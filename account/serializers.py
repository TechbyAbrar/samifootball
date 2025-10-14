from rest_framework import serializers
from .models import UserAuth
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from .account_utils import send_mail, send_otp_email, generate_otp, get_otp_expiry, generate_tokens_for_user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        fields = [
            'id', 'email', 'full_name', 'age', 'profile_pic',
            'mobile_no', 'location', 'is_verified', 'club', 'playing_level', 'is_superuser', 'is_staff', 'subscribed_plan_status',
            'date_joined', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'is_superuser', 'is_staff', 'subscribed_plan_status' 'date_joined', 'updated_at']


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    profile_pic = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = UserAuth
        fields = ['full_name', 'email', 'password', 'profile_pic']

    def create(self, validated_data):
        email = validated_data['email']
        UserAuth.objects.filter(email=email, is_verified=False).delete()

        profile_pic = validated_data.pop('profile_pic', None)
        user = UserAuth(
            email=email,
            full_name=validated_data['full_name'],
            profile_pic=profile_pic,
            is_verified=False,
        )
        user.set_password(validated_data['password'])
        user.set_otp()
        user.save()
        return user


class VerifyEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(max_length=6, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        otp = attrs.get('otp')

        try:
            user = UserAuth.objects.get(email=email)
        except UserAuth.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        if user.is_verified:
            raise serializers.ValidationError("Email is already verified.")

        if user.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")

        if user.otp_expired and timezone.now() > user.otp_expired:
            raise serializers.ValidationError("OTP has expired. Please request a new one.")

        attrs['user'] = user
        return attrs


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            user = UserAuth.objects.get(email=value)
        except UserAuth.DoesNotExist:
            raise serializers.ValidationError("No user found with this email.")

        if user.is_verified:
            raise serializers.ValidationError("This email is already verified.")

        self.user = user  # Temporarily store the user
        return value

    def validate(self, attrs):
        attrs['user'] = self.user  # Add user to validated_data
        return attrs
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Pass email as username because default backend settings expects 'username'
        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        if not user.is_active:
            raise serializers.ValidationError("Your account is disabled.")

        if not user.is_verified:
            raise serializers.ValidationError("Email is not verified. Please verify your email first.")

        attrs['user'] = user
        return attrs
    


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        try:
            user = UserAuth.objects.get(email=email)
        except UserAuth.DoesNotExist:
            raise serializers.ValidationError("No user found with this email.")
        
        if not user.is_verified:
            raise serializers.ValidationError("Email is not verified. Please verify your email first.")
        
        attrs['user'] = user
        return attrs
    
class VerifyForgetPasswordOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, required=True)

    def validate(self, attrs):
        otp = attrs.get('otp')

        try:
            user = UserAuth.objects.get(otp=otp)
        except UserAuth.DoesNotExist:
            raise serializers.ValidationError({'email': 'User not found.'})

        if user.otp != otp:
            raise serializers.ValidationError({'otp': 'Invalid OTP.'})
        
        if user.otp_expired and timezone.now() > user.otp_expired:
            raise serializers.ValidationError({'otp': 'OTP has expired.'})

        attrs['user'] = user
        return attrs

            

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if not new_password or not confirm_password:
            raise serializers.ValidationError("New Password and Confirm Password cannot be empty.")

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

        user = self.context.get('user')
        if user is None:
            raise serializers.ValidationError("User context not provided.")

        attrs['user'] = user
        return attrs
        
