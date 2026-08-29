from django.db import models


class JobApplication(models.Model):
    """A single job application, tracked end to end: applied -> interviewing -> offer/rejected."""

    STATUS_APPLIED = 'Applied'
    STATUS_INTERVIEWING = 'Interviewing'
    STATUS_OFFER = 'Offer'
    STATUS_REJECTED = 'Rejected'
    STATUS_CHOICES = [
        (STATUS_APPLIED, 'Applied'),
        (STATUS_INTERVIEWING, 'Interviewing'),
        (STATUS_OFFER, 'Offer'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_APPLIED)
    location = models.CharField(max_length=200, blank=True, default='Zurich')
    applied_date = models.DateField(null=True, blank=True)
    job_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_date', '-created_at']

    def __str__(self):
        return f'{self.title} @ {self.company}'
