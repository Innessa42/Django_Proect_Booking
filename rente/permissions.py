from rest_framework import permissions
from rente.models import User


#class IsLandlord(permissions.BasePermission):
#    def has_permission(self, request, view):
#        return request.user.is_authenticated and request.user.role == User.Role.LANDLORD
#
#
#class IsTenant(permissions.BasePermission):
#    def has_permission(self, request, view):
#        return request.user.is_authenticated and request.user.role == User.Role.TENANT
#
#
#class IsOwnerOrReadOnly(permissions.BasePermission):
#    def has_object_permission(self, request, view, obj):
#        return (
#            request.method in permissions.SAFE_METHODS or
#            obj.owner == request.user
#        )


class IsAdmin(permissions.BasePermission):
    """
    Разрешает доступ только администраторам (роль admin)
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.ADMIN


class IsLandlord(permissions.BasePermission):
    """
    Разрешает доступ только арендодателям(роль landlord)
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.LANDLORD


class IsTenant(permissions.BasePermission):
    """
    Разрешает доступ только арендаторам(роль tenant)
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.TENANT


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает изменение объекта только владельцу или администратору,
    просмотр — всем.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
                obj.owner == request.user or
                request.user.role == User.Role.ADMIN)