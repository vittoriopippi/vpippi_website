from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=255)
    scholar_url = models.URLField("Google Scholar URL", blank=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Conference(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, blank=True)
    url = models.URLField("Conference Website", blank=True)

    def __str__(self):
        return self.short_name or self.name

class Paper(models.Model):
    title = models.CharField(max_length=500)
    authors = models.ManyToManyField(Author, through='Authorship')
    abstract = models.TextField()
    pdf_url = models.URLField("PDF Link", blank=True)
    hf_url = models.URLField("HuggingFace Link", blank=True)
    github_url = models.URLField("GitHub Link", blank=True)
    project_url = models.URLField("Project/Webpage Link", blank=True)
    tags = models.ManyToManyField('Tag', related_name="papers", blank=True)
    publication_date = models.DateField()
    conference = models.ForeignKey('Conference', on_delete=models.SET_NULL, null=True, blank=True, related_name="papers")

    def ordered_authors(self):
        return self.authorship_set.select_related('author').order_by('order')

    def __str__(self):
        return self.title

class Authorship(models.Model):
    paper = models.ForeignKey('Paper', on_delete=models.CASCADE)
    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        unique_together = ('paper', 'author')
        ordering = ['order']

