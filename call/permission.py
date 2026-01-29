from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle


class CallInitiateThrottle(UserRateThrottle):
    """
    Throttle for call initiation
    Maximum 10 calls per hour per user
    """
    scope = 'call_initiate'

    def allow_request(self, request, view):
        if view.action != 'initiate':
            return True
        return super().allow_request(request, view)


class CallActionThrottle(UserRateThrottle):
    """
    Throttle for call actions (answer, reject, end)
    """
    scope = 'call_action'

    def allow_request(self, request, view):
        if view.action in ['answer', 'reject', 'end']:
            return super().allow_request(request, view)
        return True


class IsCallParticipant(permissions.BasePermission):
    """
    Permission: User must be caller or receiver
    """

    def has_object_permission(self, request, view, obj):
        return request.user in [obj.caller, obj.receiver]


class CanInitiateCall(permissions.BasePermission):
    """
    Permission: Check if user can initiate new call
    - Not in another active call
    - Has access to the room
    """

    def has_permission(self, request, view):
        if view.action != 'initiate':
            return True

        # Check concurrent calls
        from .models import Call
        active_calls = Call.objects.filter(
            caller=request.user,
            status__in=['initiated', 'ringing', 'answered']
        ).count()

        from django.conf import settings
        max_calls = getattr(settings, 'MAX_CONCURRENT_CALLS_PER_USER', 1)

        return active_calls < max_calls


# ADD TO VIEWSET

class CallViewSet(viewsets.ModelViewSet):
    # ... existing code

    permission_classes = [IsAuthenticated, CanInitiateCall]
    throttle_classes = [CallInitiateThrottle, CallActionThrottle]

    def get_permissions(self):
        """Dynamic permissions"""
        if self.action in ['answer', 'reject', 'end']:
            return [IsAuthenticated(), IsCallParticipant()]
        return super().get_permissions()