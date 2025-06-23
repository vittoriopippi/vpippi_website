from django.db import models


class Acknowledgement(models.Model):
    name_surname = models.CharField(max_length=255, unique=True)
    html = models.TextField(
        help_text="Full acknowledgement text stored as raw HTML.",
    )

    question = models.CharField(
        max_length=255,
        help_text="Security question associated with this acknowledgement.",
        null=True,
        blank=True,
    )
    password = models.CharField(
        max_length=128,
        help_text="Password for accessing the acknowledgement (consider hashing).",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name_surname

    @property
    def name(self):
        return self.name_surname.title()
    
    @property
    def first_alt(self):
        """Return the first alternative name, if any."""
        try:
            links = LinkAcknowledgement.objects.filter(ack=self)
            return links.first().alt
        except LinkAcknowledgement.DoesNotExist:
            return ""


class LinkAcknowledgement(models.Model):
    alt = models.CharField(max_length=255, unique=True)
    ack = models.ForeignKey(
        Acknowledgement, on_delete=models.CASCADE, related_name="links"
    )

    def __str__(self):
        return self.alt
