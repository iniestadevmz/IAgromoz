from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Grants access only to users with role = ADMIN."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            self.message = "Authentication required."
            return False
        if getattr(request.user, 'role', '') != 'ADMIN':
            self.message = "Access restricted to Admin users only."
            return False
        return True


class IsAdminReadDeleteOnly(BasePermission):
    """
    Admin: read all + delete any. Cannot edit content owned by others.
    Owner: full access to own content.
    Others: read only.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        is_admin = getattr(user, 'role', '') == 'ADMIN'

        if request.method in SAFE_METHODS:
            return True

        # Admin can only DELETE — never PUT/PATCH on others' content
        if is_admin and request.method == 'DELETE':
            return True
        if is_admin and request.method in ('PUT', 'PATCH'):
            self.message = "Admins cannot edit content owned by other users."
            return False

        # Owner can do anything on their own content
        owner = getattr(obj, 'author', None) or getattr(obj, 'seller', None) or getattr(obj, 'user', None)
        if owner == user:
            return True

        self.message = "You do not have permission to perform this action."
        return False


class IsFeedPublic(BasePermission):
    """
    Read (GET/HEAD/OPTIONS): unauthenticated allowed.
    Write (POST/PUT/PATCH/DELETE): authentication required.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not (request.user and request.user.is_authenticated):
            self.message = "Authentication required to write to the feed."
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        is_admin = getattr(user, 'role', '') == 'ADMIN'

        # Admin can only delete, not edit
        if is_admin and request.method == 'DELETE':
            return True
        if is_admin and request.method in ('PUT', 'PATCH'):
            self.message = "Admins cannot edit posts owned by other users."
            return False

        owner = getattr(obj, 'author', None)
        if owner == user:
            return True

        self.message = "You do not have permission to perform this action."
        return False


class IsMarketplaceAuthenticated(BasePermission):
    """All Marketplace operations require authentication."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            self.message = "Authentication required to access the marketplace."
            return False
        return True


class IsTechniquesAuthenticated(BasePermission):
    """All Techniques operations require authentication."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            self.message = "Authentication required to access techniques."
            return False
        return True


class IsSellerDashboard(BasePermission):
    """Grants access only to users with role = SELLER."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            self.message = "Authentication required."
            return False
        if getattr(request.user, 'role', '') != 'SELLER':
            self.message = "Access restricted to Seller users only."
            return False
        return True


class IsProducerDashboard(BasePermission):
    """Grants access only to users with role = PRODUCER."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            self.message = "Authentication required."
            return False
        if getattr(request.user, 'role', '') != 'PRODUCER':
            self.message = "Access restricted to Producer users only."
            return False
        return True


class IsAdminDashboard(BasePermission):
    """Grants access only to users with role = ADMIN."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            self.message = "Authentication required."
            return False
        if getattr(request.user, 'role', '') != 'ADMIN':
            self.message = "Access restricted to Admin users only."
            return False
        return True


class IsOwnerOrAdminDelete(BasePermission):
    """
    Owner (author field): full access to own content.
    Admin: DELETE only — cannot PUT/PATCH others' content.
    Others: read only.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not (user and user.is_authenticated):
            self.message = "Authentication required."
            return False

        # Owner can do anything
        if getattr(obj, 'author', None) == user:
            return True

        is_admin = getattr(user, 'role', '') == 'ADMIN'

        # Admin can only delete
        if is_admin and request.method == 'DELETE':
            return True
        if is_admin and request.method in ('PUT', 'PATCH'):
            self.message = "Admins cannot edit content owned by other users."
            return False

        self.message = "You do not have permission to perform this action."
        return False


class IsAdminOrCanSell(BasePermission):
    """
    Write: can_sell = True or ADMIN.
    Read: all authenticated.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            self.message = "Authentication required."
            return False
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if getattr(user, 'role', '') == 'ADMIN' or getattr(user, 'can_sell', False):
            return True
        self.message = "You must be authorized to sell in order to perform this action."
        return False


class IsAdminOrOwner(BasePermission):
    """
    Owner (seller field): full access.
    Admin: DELETE only — cannot PUT/PATCH others' products.
    Others: read only.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            self.message = "Authentication required."
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        is_admin = getattr(user, 'role', '') == 'ADMIN'

        # Owner can do anything
        if getattr(obj, 'seller', None) == user:
            return True

        # Admin can only delete
        if is_admin and request.method == 'DELETE':
            return True
        if is_admin and request.method in ('PUT', 'PATCH'):
            self.message = "Admins cannot edit products owned by other users."
            return False

        self.message = "You do not have permission to modify this object."
        return False

class IsNotSeller(BasePermission):
   
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return True  
        if getattr(request.user, 'role', '') == 'SELLER':
            self.message = "Sellers only have access to the marketplace."
            return False
        return True
    
    
    

        



class IsAdminOrBuyerOrSeller(BasePermission):
    """Only seller, buyer, or admin can access the transactions."""

    message = "You are not allowed to access this."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            self.message = "Authentication required."
            return False
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            user.is_staff
            or user.is_superuser
            or user == getattr(obj, 'seller', None)
            or user == getattr(obj, 'buyer', None)
        )
