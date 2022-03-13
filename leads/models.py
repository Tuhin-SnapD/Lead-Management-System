
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

class Lead(models.Model):
    state_choice=(
    ('Hot','Hot'),
    ('Medium','Medium'),
    ('Cold','Cold'),
    )
    first_name = models.CharField(max_length=25) 
    last_name = models.CharField(max_length=25) 
    age = models.IntegerField(default=0)
    email=models.EmailField(max_length=50)

    phoned = models.BooleanField(default=False)
    state = models.CharField(choices=state_choice, max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    agent= models.ForeignKey("Agent", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Agent(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE) # one to one field
    first_name = models.CharField(max_length=25) 
    last_name = models.CharField(max_length=25)
    
    def __str__(self):
        return self.user.email
    