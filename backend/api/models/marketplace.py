from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg

User = settings.AUTH_USER_MODEL


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('AGRICULTURE', 'Agricultura'),
        ('LIVESTOCK', 'Pecuária'),
    ]
    LIVESTOCK_SUBCATEGORY_CHOICES = [
        ('POULTRY', 'Aves'), ('EGGS', 'Ovos'), ('SWINE', 'Suínos'),
        ('FISH', 'Peixe'), ('CATTLE', 'Bovinos'), ('GOATS', 'Caprinos'),
        ('SHEEP', 'Ovinos'), ('BEEKEEPING', 'Apicultura'), ('OTHER', 'Outro'),
    ]
    AGRICULTURE_SUBCATEGORY_CHOICES = [
        ('CITRUS', 'Citrinos'), ('TUBERS', 'Tubérculos'), ('FRUITS', 'Frutas'),
        ('CEREALS', 'Cereais'), ('LEGUMES', 'Leguminosas'),
        ('VEGETABLES', 'Hortícolas'), ('OTHER', 'Outro'),
    ]
    BASE_UNIT_CHOICES = [
        ('UNIT', 'Unidade'),
        ('KG', 'Quilograma'),
        ('TON', 'Tonelada'),
        ('LITER', 'Litro'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # price = preço base por unidade física (base_unit)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    photo = models.ImageField(upload_to='iagromoz/products/')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=20)
    subcategory_description = models.TextField(blank=True ,null=True)
    district = models.ForeignKey('api.District', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    # stock_quantity: stock real SEMPRE em unidade base
    stock_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    # base_unit: unidade base do stock e do price
    base_unit = models.CharField(max_length=10, choices=BASE_UNIT_CHOICES)

    def __str__(self):
        return f"{self.name} - {self.seller}"

    def average_rating(self):
        return self.ratings.aggregate(avg=Avg('score'))['avg'] or 0

    def total_ratings(self):
        return self.ratings.count()


class ProductUnit(models.Model):
    """Unidade de venda flexível definida pelo vendedor."""
    SALE_UNIT_CHOICES = [
        ('UNIT',  'Unidade'),
        ('DOZEN', 'Dúzia'),
        ('FAVO',  'Favo'),
        ('BOX',   'Caixa'),
        ('SACK',  'Saco'),
        ('OTHER', 'Outro'),
    ]

    product = models.ForeignKey(Product, related_name='units', on_delete=models.CASCADE)
    # tipo de unidade — se OTHER, o vendedor preenche custom_unit_name
    unit_type = models.CharField(max_length=10, choices=SALE_UNIT_CHOICES, default='UNIT')
    # nome personalizado (obrigatório quando unit_type = OTHER)
    custom_unit_name = models.CharField(max_length=50, blank=True, null=True)
    multiplier = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    @property
    def name(self):
        """Retorna o nome efectivo da unidade."""
        if self.unit_type == 'OTHER' and self.custom_unit_name:
            return self.custom_unit_name
        return dict(self.SALE_UNIT_CHOICES).get(self.unit_type, self.unit_type)

    def __str__(self):
        return f"{self.product.name} — {self.name} (×{self.multiplier})"


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='ratings',
        null=True, blank=True
    )
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='ratings_received',
        null=True, blank=True
    )
    score = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'seller')

    def __str__(self):
        if self.product:
            return f"{self.user} rated Product {self.product} - {self.score}★"
        if self.seller:
            return f"{self.user} rated Seller {self.seller} - {self.score}★"
        return f"Rating {self.id}"


def average_seller_rating(user):
    return user.ratings_received.aggregate(avg=Avg('score'))['avg'] or 0


def total_seller_ratings(user):
    return user.ratings_received.count()


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('RESERVED', 'Reservado'),
        ('AWAITING_PAYMENT', 'Aguardando pagamento'),
        ('PAID', 'Pago'),
        ('COMPLETED', 'Concluído'),
        ('CANCELLED', 'Cancelado'),
    ]

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='RESERVED', choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    # Campos de unidade de venda
    unit = models.ForeignKey(
        ProductUnit, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transactions'
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    # quantidade convertida para unidade base (quantity × unit.multiplier)
    total_base_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Transaction {self.buyer} -> {self.product.name} - {self.status}"
