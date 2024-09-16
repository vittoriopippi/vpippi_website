from django.db import models
from pathlib import Path
import random
from PIL import Image
from django.conf import settings
from django.db.models import Q


class Competitor(models.Model):
    name = models.CharField(max_length=100)
    winner = models.BooleanField(default=False)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Prompt(models.Model):
    eng_text = models.CharField(max_length=128, unique=True)
    ita_text = models.CharField(max_length=128, blank=True)

    def answer_count_by_competitor(self):
        competitors = Competitor.objects.all()
        counts = {}
        for competitor in competitors:
            answer_count = Answer.objects.filter(
                question__sample_a__prompt=self,
                question__sample_b__prompt=self,
                winner__competitor=competitor,
            ).count()
            counts[competitor.name] = answer_count
        return counts

    def __str__(self):
        return self.eng_text
    
def content_file_name(instance, filename):
    filename = Path(filename)
    prompt = instance.prompt.eng_text.replace(' ', '_')
    rand_id = '%06x' % random.randrange(16**6)
    return Path() / 'user_study' / instance.competitor.name / prompt / f'{rand_id}{filename.suffix}'

class SampleImage(models.Model):
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    img = models.ImageField(upload_to=content_file_name, max_length=1024)
    exclude_from_study = models.BooleanField(default=False)

    @property
    def width(self):
        with self.img.open() as img:
            pil_image = Image.open(img)
            width = pil_image.width
        return width
    
    def __str__(self):
        return f'{self.competitor.name} - {self.prompt.eng_text}'

class Player(models.Model):
    name = models.CharField(max_length=100)
    accuracy = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    finished = models.BooleanField(default=False)
    correct_control_answers = models.IntegerField(default=0)

    def _accuracy(self):
        answers_count = Answer.objects.filter(player=self).filter(winner__competitor__winner=True, question__is_control=False).count()
        return answers_count
    
    def update_accuracy(self):
        self.accuracy = self._accuracy()
        self.save()

    def update_correct_control_answers(self):
        self.correct_control_answers = Answer.objects.filter(player=self, question__is_control=True, winner__competitor__winner=True).count()
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
    
    def max_score(self):
        answers = Answer.objects.all().filter(player=self, question__is_control=False)
        answers = answers.filter(Q(question__sample_a__competitor__winner=True) | Q(question__sample_b__competitor__winner=True))
        return answers.count()
    
    def __str__(self):
        return self.username()

class Question(models.Model):
    sample_a = models.ForeignKey(SampleImage, on_delete=models.CASCADE, related_name='sample_a')
    sample_b = models.ForeignKey(SampleImage, on_delete=models.CASCADE, related_name='sample_b')
    is_control = models.BooleanField(default=False)

class Answer(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    winner = models.ForeignKey(SampleImage, on_delete=models.CASCADE, related_name='winner', null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)