# Create a customized permission class for users with group managers

from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='managers').exists()
class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='customers').exists()
class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='delivery-crews').exists()