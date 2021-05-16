import datetime

from django.db import models

from .criterion import Criterion
from .present import Present
from .user import User


class History(models.Model):
    GENDER_MALE = 0
    GENDER_FEMALE = 1
    GENDER_UNKNOWN = 2
    GENDER_CHOICES = ((GENDER_MALE, 'Male'), (GENDER_FEMALE, 'Female'), (GENDER_UNKNOWN, 'Unknown'))

    present = models.ForeignKey(Present, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)
    link = models.CharField(max_length=200)
    age = models.PositiveIntegerField()
    gender = models.IntegerField(choices=GENDER_CHOICES)
    criteria = models.ManyToManyField(Criterion)

    class Meta:
        db_table = "history"
