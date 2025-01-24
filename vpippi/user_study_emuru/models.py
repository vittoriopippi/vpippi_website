from django.db import models
from pathlib import Path
import random
from PIL import Image
from django.conf import settings
from django.db.models import Q

class Competitor(models.Model):
    name = models.CharField(max_length=100)
    reference = models.BooleanField(default=False)
    winner = models.BooleanField(default=False)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
def content_file_name(instance, filename):
    filename = Path(filename)
    rand_id = '%06x' % random.randrange(16**6)
    return Path() / 'user_study' / instance.competitor.name / f'{rand_id}{filename.suffix}'

class SampleImage(models.Model):
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    img = models.ImageField(upload_to=content_file_name, max_length=1024)
    available = models.BooleanField(default=True)
    shtg_key = models.CharField(max_length=256, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['competitor', 'shtg_key'], name='unique_competitor_shtg_key')
        ]

    @property
    def size(self):
        with self.img.open() as img:
            pil_image = Image.open(img)
            size = pil_image.size
        return size
    
    def __str__(self):
        return f'{self.competitor.name} - {self.shtg_key}'

class Player(models.Model):
    name = models.CharField(max_length=100)
    accuracy = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    finished = models.BooleanField(default=False)
    correct_control_answers = models.IntegerField(default=0)

    def _accuracy(self):
        answers_count = Answer.objects.filter(player=self).filter(winner__competitor__winner=True).count()
        return answers_count
    
    def update_accuracy(self):
        self.accuracy = self._accuracy()
        self.save()

    def update_correct_control_answers(self):
        self.correct_control_answers = Answer.objects.filter(player=self, winner__competitor__winner=True).count()
        self.save()

    def username(self):
        return self.name.replace('_', ' ') + f'#{self.pk:03d}'
    
    def time_delta(self):
        answers = Answer.objects.all().filter(player=self).order_by('date')
        if answers.count() == 0:
            return None
        return answers.last().date - answers.first().date
    
    def in_progress(self):
        return not self.finished
    
    def __str__(self):
        return self.username()

class Answer(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    winner = models.ForeignKey(SampleImage, on_delete=models.CASCADE, related_name='winner', null=True)

class Skipped(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    shtg_key = models.CharField(max_length=256, default='')
    date = models.DateTimeField(auto_now_add=True)