from django.db import models

class Provincia(models.Model):
    nome=models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

class Distrito(models.Model):
    nome = models.CharField(max_length=100)
    provincia=models.ForeignKey(Provincia, related_name='distritos',on_delete=models.CASCADE)
    
    class Meta:
        unique_together =('nome','provincia')
    
    def __str__(self):
        return f"{self.nome} ({self.provincia.nome})"
    

