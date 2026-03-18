from rest_framework import serializers
from api.models.location import Provincia,Distrito

class ProvinciaSerializer (serializers.ModelSerializer):
    class Meta:
        model=Provincia
        fields = ['id','nome']

class DistritoSerializer(serializers.ModelSerializer):
    provincia =ProvinciaSerializer(read_only=True)
    
    id_provincia=serializers.PrimaryKeyRelatedField(
      queryset=Provincia.objects.all(),
      source='provincia',
      write_only=True,
      required=True
   )
    class Meta:
        model = Distrito
        fields =['id','nome','provincia','id_provincia']