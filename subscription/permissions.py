from rest_framework.permissions import BasePermission

class IsSubscribed(BasePermission):
    message = "User does not have an active subscription. Please subscribe to access this resource."

    def has_permission(self, request, view):
        subscription = getattr(request.user, 'subscription', None)
        return subscription and subscription.is_current()
