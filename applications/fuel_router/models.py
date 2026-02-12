from django.db import models


class FuelStation(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    price_per_gallon = models.DecimalField(max_digits=5, decimal_places=3)
    state = models.CharField(max_length=2)

    class Meta:
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["price_per_gallon"]),
        ]
