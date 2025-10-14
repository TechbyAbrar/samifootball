from django.urls import path
from .views import SignupView, VerifyEmailOTPView, ResendOTPView, LoginView, ForgetPasswordView, ResetPasswordView, UpdateProfileView, DashboardView, SpecificUserView, VerifyForgetPasswordOTPView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('verify-email/', VerifyEmailOTPView.as_view(), name='verify-email-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('forget-password/', ForgetPasswordView.as_view(), name='forget-password'),
    path('verify/pass/otp/', VerifyForgetPasswordOTPView.as_view(), name='forget-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('update-profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('user/<int:pk>/', SpecificUserView.as_view(), name='specific-user'),
]