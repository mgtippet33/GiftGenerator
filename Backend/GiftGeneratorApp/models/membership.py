from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


class Membership(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    premium = models.BooleanField(default=False)
    theme = models.IntegerField(default=0)
    phone_number = models.CharField(max_length=13, blank=True)
    birthday = models.DateField(blank=True, null=True)


@receiver(post_delete, sender=Membership)
def delete_user(sender, instance=None, **kwargs):
    instance.user.delete()


@receiver(post_save, sender=User)
def create_or_update_user_membership(sender, instance, created, **kwargs):
    if created:
        Membership.objects.create(user=instance)
    instance.membership.save()
