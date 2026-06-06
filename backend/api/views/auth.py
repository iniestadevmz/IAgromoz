from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from api.models.users import User, SellerProfile, ProducerProfile, UpgradeRequest
from api.serializers.users import (
    UserSerializer,
    NormalRegisterSerializer,
    ProducerRegisterSerializer,
    SellerRegisterSerializer,
    SellerProfileSerializer,
    ProducerProfileSerializer,
    ChangePasswordSerializer,
    UpgradeRequestSerializer,
    PublicProfileSerializer,
)


class UserViewSet(ModelViewSet):
    """
    Central user viewset. All registration and profile management lives here.

    Registration (public):
      POST /users/register/normal/
      POST /users/register/producer/
      POST /users/register/seller/

    Profile (authenticated):
      GET  /users/me/
      PUT  /users/me/update/
      GET  /users/me/producer-profile/
      PUT  /users/me/producer-profile/update/
      GET  /users/me/seller-profile/
      PUT  /users/me/seller-profile/update/

    Other:
      POST /users/change-password/
      POST /users/upgrade-to-producer/
      POST /users/logout/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        public_actions = ['register_normal', 'register_producer', 'register_seller']
        if self.action in public_actions:
            return [AllowAny()]
        return [IsAuthenticated()]

    def update(self, request, *args, **kwargs):
        """Only the user themselves can update their own account. Admins cannot."""
        target = self.get_object()
        if target != request.user:
            return Response(
                {"detail": "You cannot edit another user's account."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        target = self.get_object()
        if target != request.user:
            return Response(
                {"detail": "You cannot edit another user's account."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)

    # ── Registration ──────────────────────────────────────────────────────────

    @action(detail=False, methods=['post'], url_path='register/normal', permission_classes=[AllowAny])
    def register_normal(self, request):
        serializer = NormalRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='register/producer', permission_classes=[AllowAny])
    def register_producer(self, request):
        serializer = ProducerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='register/seller', permission_classes=[AllowAny])
    def register_seller(self, request):
        serializer = SellerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    # ── My profile ────────────────────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['put', 'patch'], url_path='me/update')
    def me_update(self, request):
        serializer = UserSerializer(
            request.user, data=request.data,
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ── Producer profile ──────────────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='me/producer-profile')
    def producer_profile(self, request):
        if request.user.role != 'PRODUCER':
            return Response({"detail": "Only producers have a producer profile."}, status=403)
        try:
            profile = request.user.producer_profile
        except ProducerProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)
        return Response(ProducerProfileSerializer(profile).data)

    @action(detail=False, methods=['put', 'patch'], url_path='me/producer-profile/update')
    def producer_profile_update(self, request):
        if request.user.role != 'PRODUCER':
            return Response({"detail": "Only producers can update a producer profile."}, status=403)
        try:
            profile = request.user.producer_profile
        except ProducerProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)
        serializer = ProducerProfileSerializer(
            profile, data=request.data, partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ── Seller profile ────────────────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='me/seller-profile')
    def seller_profile(self, request):
        if request.user.role != 'SELLER':
            return Response({"detail": "Only sellers have a seller profile."}, status=403)
        try:
            profile = request.user.seller_profile
        except SellerProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)
        return Response(SellerProfileSerializer(profile).data)

    @action(detail=False, methods=['put', 'patch'], url_path='me/seller-profile/update')
    def seller_profile_update(self, request):
        if request.user.role != 'SELLER':
            return Response({"detail": "Only sellers can update a seller profile."}, status=403)
        try:
            profile = request.user.seller_profile
        except SellerProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)
        serializer = SellerProfileSerializer(
            profile, data=request.data, partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    #── Full Profile───────────────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='me/full-profile')
    def full_profile(self, request):
        user = request.user

    
        user_data = UserSerializer(user).data

    
        producer_data = None
        seller_data = None

        # Producer profile
        if user.role == 'PRODUCER':
            try:
                producer_data = ProducerProfileSerializer(user.producer_profile).data
            except ProducerProfile.DoesNotExist:
                producer_data = None

        # Seller profile
        if user.role == 'SELLER':
            try:
                seller_data = SellerProfileSerializer(user.seller_profile).data
            except SellerProfile.DoesNotExist:
                seller_data = None

        return Response({
            "user": user_data,
            "producer_profile": producer_data,
            "seller_profile": seller_data
        })

    #Show profile

    @action(detail=True, methods=['get'], url_path='public-profile', permission_classes=[AllowAny])
    def public_profile(self, request, pk=None):
        user = self.get_object()
        serializer = PublicProfileSerializer(user)
        return Response(serializer.data)

    # ── Upgrade NORMAL → PRODUCER (request, pending admin approval) ──────────

    @action(detail=False, methods=['post'], url_path='upgrade-to-producer')
    def upgrade_to_producer(self, request):
        """
        NORMAL user submits an upgrade request.
        Creates an UpgradeRequest with status=PENDING and notifies all admins.
        The role is NOT changed yet — admin must approve first.
        """
        if request.user.role != 'NORMAL':
            return Response({"detail": "Only NORMAL users can request an upgrade."}, status=400)

        if hasattr(request.user, 'upgrade_request'):
            existing = request.user.upgrade_request
            if existing.status == 'PENDING':
                return Response({"detail": "You already have a pending upgrade request."}, status=400)
            if existing.status == 'APPROVED':
                return Response({"detail": "Your upgrade has already been approved."}, status=400)
            # If REJECTED, allow re-submission by deleting old request
            existing.delete()

        serializer = UpgradeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        # Signal fires automatically and notifies all admins

        return Response(
            {"detail": "Upgrade request submitted. Awaiting admin approval."},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], url_path='upgrade-to-producer/status')
    def upgrade_request_status(self, request):
        """Check the status of the current user's upgrade request."""
        try:
            req = request.user.upgrade_request
        except UpgradeRequest.DoesNotExist:
            return Response({"detail": "No upgrade request found."}, status=404)
        return Response(UpgradeRequestSerializer(req).data)

    @action(detail=True, methods=['post'], url_path='approve-upgrade')
    def approve_upgrade(self, request, pk=None):
        """
        Admin approves or rejects an upgrade request.
        POST /users/{user_id}/approve-upgrade/
        Body: {"decision": "APPROVED"} or {"decision": "REJECTED"}
        """
        from api.permissions import IsAdmin
        if not IsAdmin().has_permission(request, self):
            return Response({"detail": "Only admins can approve upgrades."}, status=403)

        target_user = self.get_object()
        try:
            upgrade_req = target_user.upgrade_request
        except UpgradeRequest.DoesNotExist:
            return Response({"detail": "No upgrade request found for this user."}, status=404)

        if upgrade_req.status != 'PENDING':
            return Response({"detail": f"Request already {upgrade_req.status.lower()}."}, status=400)

        decision = request.data.get('decision')
        if decision not in ['APPROVED', 'REJECTED']:
            return Response({"detail": "Use 'APPROVED' or 'REJECTED'."}, status=400)

        from django.utils import timezone
        upgrade_req.status = decision
        upgrade_req.reviewed_at = timezone.now()
        upgrade_req.save()  # signal fires here and notifies the user

        if decision == 'APPROVED':
            target_user.role = 'PRODUCER'
            target_user.save()
            ProducerProfile.objects.get_or_create(
                user=target_user,
                defaults={
                    'contact': upgrade_req.contact,
                    'farm_address': upgrade_req.farm_address,
                }
            )

        return Response({"detail": f"Upgrade request {decision.lower()}."})


    # ── Change password ───────────────────────────────────────────────────────

    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({"detail": "Password updated successfully."})

    # ── Logout ────────────────────────────────────────────────────────────────

    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=400)
        try:
            RefreshToken(refresh_token).blacklist()
            try:
                from api.services.audit_logger import log_action
                from api.models.audit import AuditLog
                log_action(
                    user=request.user,
                    action=AuditLog.Action.LOGOUT,
                    resource="Auth",
                    resource_id=str(request.user.pk),
                    status=AuditLog.Status.SUCCESS,
                    detail=f"User '{request.user.email}' logged out.",
                    request=request,
                )
            except Exception:
                pass
            return Response({"detail": "Logged out successfully."})
        except Exception:
            return Response({"detail": "Invalid or expired token."}, status=400)
