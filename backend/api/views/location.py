from api.models.location import Provincia, Distrito
from api.serializers.location import ProvinciaSerializer, DistritoSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from api.permissions import IsAdminUserCustom


class ProvinciaViewSet(ModelViewSet):
    queryset = Provincia.objects.all()
    serializer_class = ProvinciaSerializer
    def get_permissions(self):
            if self.action in ['list', 'retrieve']:
                return [AllowAny()]
            return [IsAdminUserCustom()]

class DistritoViewSet(ModelViewSet):
    queryset =Distrito.objects.all()
    serializer_class = DistritoSerializer
    print("TOTAL DISTRITOS:", queryset.count())
    

    def get_queryset(self):
        id_provincia = self.request.query_params.get('id')
        print("ID PROVINCIA RECEBIDO:", id)
        if id_provincia:
            filtrado=Distrito.objects.filter (provincia=id_provincia)

            print("DISTRITOS FILTRADOS:", filtrado.count())
            for i in filtrado:
                 print(i)

            return  filtrado
        
        return Distrito.objects.all()

    def get_permissions(self):
            if self.action in ['list', 'retrieve']:
                return [AllowAny()]       # só leitura pública
            return [IsAdminUserCustom()]    # criar, editar, apagar