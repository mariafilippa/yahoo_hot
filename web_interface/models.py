from django.db import models


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    cid = models.IntegerField()
    done = models.BooleanField(default=False)
    zone = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='sub')


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    url = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey('web_interface.category', on_delete=models.CASCADE, related_name='products')
