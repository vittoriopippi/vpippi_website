from django.db import models
from urllib.parse import quote
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
            # ensure it's a string
            phone_bytes = phone.encode('utf-8')
            # URL-safe base64, then strip any '=' padding
            token = base64.urlsafe_b64encode(phone_bytes).decode('ascii').rstrip('=')
            return token
        except (TypeError, UnicodeEncodeError):
            return None

    @staticmethod
    def base64_to_phone(token):
        try:
            # restore padding
            padding = '=' * (-len(token) % 4)
            phone_bytes = base64.urlsafe_b64decode(token + padding)
            return phone_bytes.decode('utf-8')
        except (TypeError, base64.binascii.Error, UnicodeDecodeError):
            return None
        
    def welcome_msg(self):
        name = self.name.split()[0]
        if self.fuorisede:
            msg = f"Hi {name}, welcome to the party! We are looking forward to seeing you!"
        else:
            msg = f'Ciao {name}, benvenuto alla festa! Non vediamo l\'ora di vederti!'
        return quote(msg)

    def __str__(self):
        return self.name