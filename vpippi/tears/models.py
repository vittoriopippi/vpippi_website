from django.db import models
from datetime import datetime

HAPPY = 'h'
BORED = 'b'
SAD = 's'

CHOICES = [
    (HAPPY, 'Happy'),
    (BORED, 'Bored'),
    (SAD, 'Sad'),
]

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

class Tears(models.Model):
    status = models.CharField(max_length=1, choices=CHOICES, default=HAPPY)
    quantity = models.IntegerField()
    description = models.CharField(max_length=280)

    def quantity_str(self):
        return '💧' * self.quantity

    def status_str(self):
        if self.status == HAPPY:
            return "😊"
        elif self.status == BORED:
            return "🥱"
        elif self.status == SAD:
            return "😭"
        else:
            return "😵‍💫"
        
    def __str__(self):
        return f"{self.status_str()} {self.quantity_str()} {self.description[:16]}"

class Day(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tears = models.ManyToManyField(Tears, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=CHOICES)
    description = models.CharField(max_length=280, blank=True)

    def day_tears(self):
        return self.tears.all()
    
    def has_description(self):
        return self.description != ""
    
    def passed_time(self):
        return (datetime.now().date() - self.date).days
    
    def card_class(self):
        if self.status == HAPPY:
            return "card_happy"
        elif self.status == BORED:
            return "card_bored"
        elif self.status == SAD:
            return "card_sad"
        else:
            return ""
    
    def __str__(self):
        txt = self.date.strftime("%d %B")
        txt = txt.replace("January", "Gennaio")
        txt = txt.replace("February", "Febbraio")
        txt = txt.replace("March", "Marzo")
        txt = txt.replace("April", "Aprile")
        txt = txt.replace("May", "Maggio")
        txt = txt.replace("June", "Giugno")
        txt = txt.replace("July", "Luglio")
        txt = txt.replace("August", "Agosto")
        txt = txt.replace("September", "Settembre")
        txt = txt.replace("October", "Ottobre")
        txt = txt.replace("November", "Novembre")
        txt = txt.replace("December", "Dicembre")
        return txt
