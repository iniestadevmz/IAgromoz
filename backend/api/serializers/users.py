from rest_framework import serializers
from api.models.users import User
from api.models.location import Distrito
from  .location import DistritoSerializer

class UserSerializer(serializers.ModelSerializer):

   distrito=DistritoSerializer(read_only=True)
   id_distrito=serializers.PrimaryKeyRelatedField(
      queryset=Distrito.objects.all(),
      source='distrito',
      write_only=True,
      required=True
   )
   nome_completo = serializers.CharField(source='get_full_name', read_only=True)  # novo campo
   

   password = serializers.CharField(write_only=True,required=True)

   class Meta:
      model= User
      fields =['id','email','first_name','last_name','distrito','id_distrito','password','tipos','pode_vender','nome_completo']
      read_only_fields=['id','tipos']
    
   def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  
        user.save()
        return user
   

   def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  
        instance.save()
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha actual incorreta.")
        return value

       
      
