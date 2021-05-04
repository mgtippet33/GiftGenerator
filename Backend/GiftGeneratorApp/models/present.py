from django.db import models
from .criterion import Criterion
from .holiday import Holiday


class Present(models.Model):
    name = models.CharField(max_length=50)
    link = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    desc = models.CharField(max_length=400, blank=True)
    criteria = models.ManyToManyField(Criterion)
    holidays = models.ManyToManyField(Holiday)

    def __str__(self):
        return self.name
