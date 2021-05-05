from django.db import models


class Criterion(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "criterion"

    def __str__(self):
        return self.name
