from django.db import models
from django.contrib.auth.models import User


class Holiday(models.Model):
    name = models.CharField(max_length=50)
    date = models.DateField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f'{self.name} {self.date}'
