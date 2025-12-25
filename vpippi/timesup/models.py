from django.db import models
from django.utils import timezone
import random
import string

# Create your models here.

class Game(models.Model):
    ROUND_CHOICES = [
        (1, 'Round 1: Open Description'),
        (2, 'Round 2: One Word'),
        (3, 'Round 3: The Mime'),
    ]
    
    STATUS_CHOICES = [
        ('setup', 'Setup'),
        ('playing', 'Playing'),
        ('finished', 'Finished'),
    ]
    
    code = models.CharField(max_length=6, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='setup')
    current_round = models.IntegerField(choices=ROUND_CHOICES, default=1)
    current_team_index = models.IntegerField(default=0)
    current_turn_start = models.DateTimeField(null=True, blank=True)
    turn_duration = models.IntegerField(default=30)  # seconds
    
    def __str__(self):
        return f"Game {self.code}"
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_code():
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Game.objects.filter(code=code).exists():
                return code
    
    def get_current_team(self):
        teams = list(self.teams.all().order_by('id'))
        if teams and self.current_team_index < len(teams):
            return teams[self.current_team_index]
        return None
    
    def next_team(self):
        teams_count = self.teams.count()
        if teams_count > 0:
            self.current_team_index = (self.current_team_index + 1) % teams_count
            self.save()
    
    def start_round(self, round_number):
        self.current_round = round_number
        self.current_team_index = 0
        self.status = 'playing'
        
        # Reset all cards for the new round and shuffle their order
        cards = list(self.cards.all())
        random.shuffle(cards)
        
        for idx, card in enumerate(cards):
            card.guessed_in_current_round = False
            card.round_order = idx  # Use round_order for the shuffled position
            card.save()
        
        self.save()
    
    def next_round(self):
        if self.current_round < 3:
            self.start_round(self.current_round + 1)
        else:
            self.status = 'finished'
            self.save()


class Team(models.Model):
    COLOR_CHOICES = [
        ('red', 'Red Team'),
        ('blue', 'Blue Team'),
        ('green', 'Green Team'),
        ('yellow', 'Yellow Team'),
    ]
    
    COLOR_GRADIENTS = {
        'red': 'linear-gradient(135deg, #e53935 0%, #c62828 100%)',
        'blue': 'linear-gradient(135deg, #1e88e5 0%, #1565c0 100%)',
        'green': 'linear-gradient(135deg, #43a047 0%, #2e7d32 100%)',
        'yellow': 'linear-gradient(135deg, #fdd835 0%, #f9a825 100%)',
    }
    
    COLOR_TEXT = {
        'red': '#ffffff',
        'blue': '#ffffff',
        'green': '#ffffff',
        'yellow': '#333333',
    }
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='teams')
    color = models.CharField(max_length=10, choices=COLOR_CHOICES)
    score_round1 = models.IntegerField(default=0)
    score_round2 = models.IntegerField(default=0)
    score_round3 = models.IntegerField(default=0)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['game', 'color']
    
    def __str__(self):
        return f"{self.get_color_display()} (Game {self.game.code})"
    
    @property
    def name(self):
        return self.get_color_display()
    
    @property
    def background_gradient(self):
        return self.COLOR_GRADIENTS.get(self.color, '')
    
    @property
    def text_color(self):
        return self.COLOR_TEXT.get(self.color, '#ffffff')
    
    @property
    def total_score(self):
        return self.score_round1 + self.score_round2 + self.score_round3
    
    def add_score(self, round_number, points=1):
        if round_number == 1:
            self.score_round1 += points
        elif round_number == 2:
            self.score_round2 += points
        elif round_number == 3:
            self.score_round3 += points
        self.save()


class Player(models.Model):
    ROLE_CHOICES = [
        ('cluegiver', 'Cluegiver'),
        ('guesser', 'Guesser'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='guesser')
    
    def __str__(self):
        return f"{self.name} ({self.team.name})"


class Card(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='cards')
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    guessed_in_current_round = models.BooleanField(default=False)
    round_order = models.IntegerField(default=0)  # Shuffled order for current round
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name} (Game {self.game.code})"


class GameRound(models.Model):
    """Track cards guessed by each team in each round"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='round_records')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='round_records')
    round_number = models.IntegerField()
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    guessed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['guessed_at']
    
    def __str__(self):
        return f"Round {self.round_number}: {self.card.name} by {self.team.name}"
