from django.db import models


class Acknowledgement(models.Model):
    name_surname = models.CharField(max_length=255, unique=True)
    html = models.TextField(
        help_text="Full acknowledgement text stored as raw HTML.",
    )

    question = models.CharField(
        max_length=255,
        help_text="Security question associated with this acknowledgement.",
    )
    password = models.CharField(
        max_length=128,
        help_text="Password for accessing the acknowledgement (consider hashing).",
    )

    def __str__(self):
        return self.name_surname

    @property
    def name(self):
        return self.name_surname.title()


class LinkAcknowledgement(models.Model):
    alt = models.CharField(max_length=255, unique=True)
    ack = models.ForeignKey(
        Acknowledgement, on_delete=models.CASCADE, related_name="links"
    )

    def __str__(self):
        return self.alt
