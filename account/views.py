from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import (
    SignupSerializer, VerifyEmailOTPSerializer,
    UserSerializer, ResendOTPSerializer, LoginSerializer,
    ForgetPasswordSerializer, ResetPasswordSerializer
)
from .account_utils import generate_otp, send_otp_email
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .account_utils import generate_tokens_for_user
from .throttlings import (LoginThrottle, SignupThrottle, VerifyOTPThrottle, ResendOTPThrottle, ForgetPassThrottle, ResetPassThrottle)
from django.contrib.auth import authenticate
from django.db import transaction
from .account_permissions import  IsOwnerOrSuperuser, IsSuperUserOrReadOnly
from rest_framework.permissions import IsAuthenticated
from .models import UserAuth

import logging
logger = logging.getLogger(__name__)

from django.db import transaction
# Create your views here.
from rest_framework.parsers import MultiPartParser, FormParser

class SignupView(APIView):
    permission_classes = [AllowAny]
    # throttle_classes = [SignupThrottle]
    parser_classes = [MultiPartParser, FormParser]  # Allow file uploads
    
    @transaction.atomic
    def post(self, request):
        email = request.data.get('email')
        print(f"Received email: {email}")  # Debugging line to check email input
        password = request.data.get('password')
        print(f"Received password: {password}")  # Debugging line to check password input
        try:
            user = authenticate(email=email, password=password)
            print(user)
            if not user.is_verified:
                user.delete()
        except:
            pass
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                send_otp_email(user.email, user.otp)
                tokens = generate_tokens_for_user(user)

                logger.info(f"Signup successful. OTP sent to {user.email}")

                return Response({
                    'sucess': True,
                    'message': 'Signup successful. OTP sent to your email.',
                    'access_token': tokens['access'],
                    # 'refresh_token': tokens['refresh'],
                    'profile_pic_url': request.build_absolute_uri(user.profile_pic.url) if user.profile_pic else None
                    
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Signup error: {str(e)}", exc_info=True)
                return Response({
                    'error': 'Internal server error. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.warning(f"Signup failed due to validation: {serializer.errors}")
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



# class VerifyEmailOTPView(APIView):
#     permission_classes = [AllowAny]
#     # throttle_classes = [VerifyOTPThrottle]

#     @transaction.atomic
#     def post(self, request):
#         serializer = VerifyEmailOTPSerializer(data=request.data)

#         if serializer.is_valid():
#             try:
#                 user = serializer.validated_data['user']
#                 user.is_verified = True
#                 user.otp = None
#                 user.otp_expired = None
#                 user.save()

#                 tokens = generate_tokens_for_user(user)

#                 logger.info(f"Email verified for user: {user.email}")
#                 return Response({
#                     'success': True,
#                     'message': 'Email verified successfully.',
#                     'access_token': tokens['access'],
#                     # 'refresh_token': tokens['refresh']
#                 }, status=status.HTTP_200_OK)

#             except Exception as e:
#                 logger.error(f"Email verification error: {str(e)}", exc_info=True)
#                 return Response({
#                     'error': 'Email verification failed. Please try again later.'
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         logger.warning(f"Email verification failed: {serializer.errors}")
#         return Response({
#             'errors': serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailOTPView(APIView):
    permission_classes = [AllowAny]
    # throttle_classes = [VerifyOTPThrottle]

    @transaction.atomic
    def post(self, request):
        serializer = VerifyEmailOTPSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user = serializer.validated_data['user']
                user.is_verified = True
                user.otp = None
                user.otp_expired = None
                user.save()

                tokens = generate_tokens_for_user(user)

                logger.info(f"Email verified for user: {user.email}")
                return Response({
                    'success': True,
                    'message': 'Email verified successfully.',
                    'access_token': tokens['access'],
                    # 'refresh_token': tokens['refresh']
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Email verification error: {str(e)}", exc_info=True)
                return Response({
                    'error': 'Email verification failed. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.warning(f"Email verification failed: {serializer.errors}")
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)





class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    # throttle_classes = [ResendOTPThrottle]

    @transaction.atomic
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.validated_data['user']
                user.set_otp()
                user.save()

                send_otp_email(user.email, user.otp)
                logger.info(f"New OTP sent to {user.email}")

                return Response({
                    'success': True,
                    'message': 'A new OTP has been sent to your email.'
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.exception("Error while resending OTP")  # cleaner log
                return Response({
                    'error': 'Failed to resend OTP. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.warning(f"Resend OTP validation failed: {serializer.errors}")
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    # throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.validated_data['user']
                tokens = generate_tokens_for_user(user)

                logger.info(f"User {user.email} logged in successfully.")

                return Response({
                    'success': True,
                    'message': 'Login successful!',
                    'access_token': tokens['access'],
                    'refresh_token': tokens['refresh'],
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Unexpected error during login for {request.data.get('email')}: {str(e)}", exc_info=True)
                return Response({
                    'error': 'An unexpected error occurred. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.warning(f"Login validation failed: {serializer.errors}")
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
        
class ForgetPasswordView(APIView):
    permission_classes = [AllowAny]
    # throttle_classes = [ForgetPassThrottle]
    
    def post(self, request):
        serializer = ForgetPasswordSerializer(data = request.data)
        
        if serializer.is_valid():
            try:
                user = serializer.validated_data['user']
                user.set_otp()
                user.save()
                
                send_otp_email(user.email, user.otp)
                logger.info(f"OTP for password reset sent to {user.email}")
                return Response({
                    'success': True,
                    'message': 'OTP for password reset sent to your email.'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error while sending OTP for password reset: {str(e)}", exc_info=True)
                return Response({
                    'error': 'Failed to send OTP for password reset. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        logger.warning(f"Forget password validation failed: {serializer.errors}")
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)  
        
from .serializers import VerifyForgetPasswordOTPSerializer

class VerifyForgetPasswordOTPView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = VerifyForgetPasswordOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate access token only (no refresh)
            token = generate_tokens_for_user(user)
            access_token = token['access']

            return Response({
                'success': True,
                'message': 'OTP verified. You may now reset your password.',
                'access_token': access_token,
            }, status=status.HTTP_200_OK)

        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrSuperuser]  
    # throttle_classes = [ResetPassThrottle]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data, context={'user': request.user})

        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']

            try:
                user.set_password(new_password)
                user.save()
                logger.info(f"Password reset successfully for user: {user.email}")
                return Response({'success':True,'message': 'Password reset successful.'}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error resetting password for {user.email}: {str(e)}", exc_info=True)
                return Response({'error': 'Failed to reset password. Please try again later.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.warning(f"Reset password validation failed for user {request.user.email if request.user else 'Anonymous'}: {serializer.errors}")
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    
class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrSuperuser]
    
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info(f"User profile updated successfully for {user.email}")
                return Response({
                    'success':True,
                    'message': 'Profile updated successfully.',
                    'user': serializer.data
                    }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error updating user profile for {user.email}: {str(e)}", exc_info=True)
                return Response({'error': 'Failed to update profile. Please try again later.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.warning(f"Profile update validation failed for {user.email}: {serializer.errors}")
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

# class DashboardView(APIView):
#     permission_classes = [IsOwnerOrSuperuser]
#     # throttle_classes = [CustomUserThrottle]

#     def get(self, request):
#         user = request.user

#         if not user.is_superuser:
#             logger.warning(f'Unauthorized dashboard access by user: {user.id}')
#             return Response({'message': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

#         users = UserAuth.objects.all()
#         total_users = users.count()
#         verified_users = users.filter(is_verified=True).count()
#         unverified_users = total_users - verified_users
#         serializer = UserSerializer(users, many=True)

#         logger.info(f'Superuser {user.id} accessed dashboard.')

#         return Response({
#             'success': True,
#             'message': 'Dashboard data retrieved successfully.',
#             'total_users': total_users,
#             'verified_users': verified_users,
#             'unverified_users': unverified_users,
#             'user_list': serializer.data,
#         }, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from tickets.models import TicketPurchase
from subscription.models import UserSubscription
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class DashboardView(APIView):
    permission_classes = [IsOwnerOrSuperuser]

    def get(self, request):
        user = request.user

        if not user.is_superuser:
            logger.warning(f'Unauthorized dashboard access by user: {user.id}')
            return Response({'message': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        # User stats - only 2 queries total here
        total_users = UserAuth.objects.count()
        verified_users = UserAuth.objects.filter(is_verified=True).count()
        unverified_users = total_users - verified_users

        # Serialize only if necessary - consider lazy or limit for large users list
        serializer = UserSerializer(UserAuth.objects.all(), many=True)

        # Ticket purchase earnings - single aggregate query, no joins except F('ticket__price')
        ticket_earnings = (
            TicketPurchase.objects
            .filter(payment_status='succeeded')
            .aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('ticket__price') * F('quantity'),
                        output_field=DecimalField(max_digits=20, decimal_places=2)
                    )
                )
            )
        )['total'] or Decimal('0.00')

        # Subscription earnings - sum monthly_price for active subscriptions, single query
        total_subscription_earnings = (
            UserSubscription.objects
            .filter(is_active=True)
            .aggregate(total=Sum('plan__monthly_price'))
        )['total'] or Decimal('0.00')

        # Count of active subscriptions - single query
        total_subscribed_users = UserSubscription.objects.filter(is_active=True).count()
        
        logger.info(f'Superuser {user.id} accessed dashboard.')

        return Response({
            'success': True,
            'message': 'Dashboard data retrieved successfully.',
            'total_users': total_users,
            'verified_users': verified_users,
            'unverified_users': unverified_users,
            'total_earning': float(ticket_earnings + total_subscription_earnings),
            'total_subscribed_users': total_subscribed_users,
            'user_list': serializer.data,
        }, status=status.HTTP_200_OK)


            
class SpecificUserView(APIView):
    permission_classes = [IsOwnerOrSuperuser]

    def get(self, request, pk):
        user = request.user
        if not user.is_superuser:
            logger.warning(f'Unauthorized detail access by user: {user.id}')
            return Response({'message': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user_obj = UserAuth.objects.get(pk=pk)
            serializer = UserSerializer(user_obj)
            logger.info(f'Superuser {user.id} accessed data for user {pk}')
            return Response({
                'success': True,
                'message': 'User data retrieved successfully.',
                'user': serializer.data
                }, status=status.HTTP_200_OK)
        except UserAuth.DoesNotExist:
            logger.error(f'User with ID {pk} not found.')
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)