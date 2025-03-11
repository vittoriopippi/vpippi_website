from django.db import models
import base64

class Invite(models.Model):
    YES = 'YE'
    NO = 'NO'
    PENDING = 'PD'
    PLUS = '+1'
    STATES = [
        (PENDING, 'Pending'),
        (NO, 'No'),
        (YES, 'Yes'),
        (PLUS, 'Yes plus one')
    ]
    name = models.CharField(max_length=64)
    phone = models.CharField(max_length=32, unique=True)
    code = models.CharField(max_length=32, unique=True)
    phone_suffix = models.CharField(max_length=6, default='+39')
    state = models.CharField(max_length=2, choices=STATES, default=PENDING)
    date_modified = models.DateTimeField(auto_now=True)
    fuorisede = models.BooleanField(default=False)
    foreign = models.BooleanField(default=False)

    @staticmethod
    def phone_to_base64(phone):
        try:
            phone = int.to_bytes(int(phone), 6, 'big')
            phone = base64.b64encode(phone).decode('utf-8')
        except:
            return None
        return phone
    
    @staticmethod
    def base64_to_phone(phone):
        try:
            phone = str(int.from_bytes(base64.b64decode(phone), byteorder='big'))
        except:
            return None
        return phone

    def __str__(self):
        return self.name