from django.db import models


class Province(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, related_name='districts', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'province')

    def __str__(self):
        return f"{self.name} ({self.province.name})"
