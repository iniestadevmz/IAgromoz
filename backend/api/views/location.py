from api.models.location import Province, District
from api.serializers.location import ProvinceSerializer, DistrictSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from api.permissions import IsAdmin
from api.services.audit_logger import log_action



class ProvinceViewSet(ModelViewSet):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdmin()]


class DistrictViewSet(ModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer

    def get_queryset(self):
        province_id = self.request.query_params.get('id')
        if province_id:
            return District.objects.filter(province=province_id)
        return District.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdmin()]
