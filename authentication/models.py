from tabnanny import verbose
from django.db import models

# Create your models here.
STATUS_CHOICES = [
    ('a', 'approved'),
    ('n', 'not approved'),
    ('p','pending'),
]
class user(models.Model):
    username = models.CharField(max_length=50)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=200)
    confirmpassword = models.CharField(max_length=200)
    phone_no =models.IntegerField(verbose_name="phonenumber",default=None, null=True,blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    def __str_(self):
        return self.title
    
    


