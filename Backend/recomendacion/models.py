from django.db import models

class Plato(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.nombre

class Recomendacion(models.Model):
    telegram_id = models.BigIntegerField()
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE)
    motivo = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recomendación de {self.plato.nombre} para {self.telegram_id}"
