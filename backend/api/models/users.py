from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from api.models.location import Distrito

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O email é obrigatório")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
       
        extra_fields['tipos'] = 'ADMIN'
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    #bio = models.TextField(blank=True, null=True)
    #avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    distrito = models.ForeignKey(Distrito, null=True, blank=True, on_delete=models.SET_NULL)
    tipos = models.CharField(max_length=20, choices=[('ADMIN','Administrador'), ('AGRICULTOR','Agricultor')], default='AGRICULTOR')
    pode_vender = models.BooleanField(default=False)  
   

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    


