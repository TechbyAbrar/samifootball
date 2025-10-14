from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

f"""
UserRateThrottle = used for authenticated users, allowing them a higher rate limit than anonymous users.
AnonRateThrottle = used for anonymous users, providing a lower rate limit to prevent abuse.
"""

class SignupThrottle(AnonRateThrottle):
    rate = '10/hour' 
    
class VerifyOTPThrottle(AnonRateThrottle):
    rate = '10/hour' 


class ResendOTPThrottle(AnonRateThrottle):
    rate = '10/hour'  
    
    
class LoginThrottle(AnonRateThrottle):
    rate = '15/hour'
    scope = 'login'


class ForgetPassThrottle(AnonRateThrottle):
    rate = '15/hour'
    scope = 'login'
    
class ResetPassThrottle(UserRateThrottle):
    rate = '10/hour'