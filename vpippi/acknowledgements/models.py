from django.db import models

class Acknowledgement(models.Model):
    name_surname = models.CharField(max_length=255, unique=True)
    text = models.TextField()

    def __str__(self):
        return self.name_surname
    
    @property
    def name(self):
        return self.name_surname.title()

class LinkAcknowledgement(models.Model):
    alt = models.CharField(max_length=255, unique=True)
    ack = models.ForeignKey(Acknowledgement, on_delete=models.CASCADE)

class FakeAcknowledgement(models.Model):
    text = models.TextField()

