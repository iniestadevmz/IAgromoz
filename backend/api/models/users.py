from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from api.models.location import District


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
        extra_fields['role'] = 'ADMIN'
        if 'first_name' not in extra_fields:
            raise ValueError("Campo first_name é obrigatório")
        elif 'first_name' not in extra_fields:
            raise ValueError("Campo last_name é obrigatório")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('NORMAL', 'Normal'),
        ('PRODUCER', 'Produtor'),
        ('SELLER', 'Vendedor'),
    ]

    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ]

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    profile_photo = models.ImageField(upload_to='iagromoz/fotos_de_perfil/', blank=True, null=True)
    district = models.ForeignKey(District, null=True, on_delete=models.SET_NULL)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='NORMAL')
    can_sell = models.BooleanField(default=False)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','last_name']

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    def save(self, *args, **kwargs):
        self.can_sell = self.role in ('PRODUCER', 'SELLER')
        super().save(*args, **kwargs)


class SellerProfile(models.Model):
    SELLER_TYPE_CHOICES = [
        ('COMPANY', 'Empresa'),
        ('COOPERATIVE', 'Cooperativa'),
        ('INDIVIDUAL', 'Individual'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    seller_type = models.CharField(max_length=20, choices=SELLER_TYPE_CHOICES)
    store_name = models.CharField(max_length=200)
    nuit = models.CharField(max_length=50, blank=True)
    contact = models.CharField(max_length=50)
    store_address = models.TextField()


class ProducerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='producer_profile')
    contact = models.CharField(max_length=50)
    farm_address = models.TextField()


class UpgradeRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('APPROVED', 'Aprovado'),
        ('REJECTED', 'Rejeitado'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='upgrade_request')
    contact = models.CharField(max_length=50)
    farm_address = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} — {self.status}"
