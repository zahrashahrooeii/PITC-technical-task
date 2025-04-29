from rest_framework import permissions
from .models import AccountManager, Customer, Order, Service

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to create/edit service providers.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        # Write permissions are only allowed to admin users
        return request.user.is_staff

class IsAccountManagerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow account managers to access their own customers and orders.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or 
            hasattr(request.user, 'accountmanager')
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        if not hasattr(request.user, 'accountmanager'):
            return False

        if isinstance(obj, Customer):
            return obj.account_manager == request.user.accountmanager
        elif isinstance(obj, Order):
            return obj.customer.account_manager == request.user.accountmanager
        elif isinstance(obj, Service):
            # Check if the service provider is associated with the account manager
            return obj.service_provider in request.user.accountmanager.service_providers.all()
        
        return False 