from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Sum
from .models import Game, Team, Player, Card, GameRound
import json
import random
import os
from django.conf import settings

# Create your views here.

def index(request):
    """Home page - create or join a game"""
    return render(request, 'timesup/index.html')


def create_game(request):
    """Create a new game"""
    if request.method == 'POST':
        game = Game.objects.create()
        return redirect('timesup:setup', code=game.code)
    return redirect('timesup:index')


def join_game(request):
    """Join an existing game"""
    if request.method == 'POST':
        code = request.POST.get('code', '').upper()
        try:
            game = Game.objects.get(code=code)
            return redirect('timesup:setup', code=game.code)
        except Game.DoesNotExist:
            return render(request, 'timesup/index.html', {'error': 'Game not found'})
    return redirect('timesup:index')


def setup(request, code):
    """Setup page - configure teams and cards"""
    game = get_object_or_404(Game, code=code)
    
    if request.method == 'POST':
        # Process setup data
        data = json.loads(request.body)
        
        # Set turn duration if provided
        turn_duration = data.get('turn_duration', 30)
        game.turn_duration = turn_duration
        game.save()
        
        # Create teams
        for idx, team_data in enumerate(data.get('teams', [])):
            team = Team.objects.create(
                game=game,
                color=team_data['color'],
                order=idx
            )
            # Create players
            for player_data in team_data.get('players', []):
                Player.objects.create(
                    team=team,
                    name=player_data['name']
                )
        
        # Create cards
        for idx, card_name in enumerate(data.get('cards', [])):
            Card.objects.create(
                game=game,
                name=card_name,
                order=idx
            )
        
        return JsonResponse({'success': True, 'redirect': f'/timesup/{code}/lobby/'})
    
    teams = game.teams.all()
    cards = game.cards.all()
    
    # Load available words from file
    words_file = os.path.join(os.path.dirname(__file__), 'words.txt')
    available_words = []
    try:
        with open(words_file, 'r', encoding='utf-8') as f:
            available_words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        available_words = []
    
    return render(request, 'timesup/setup.html', {
        'game': game,
        'teams': teams,
        'cards': cards,
        'available_words': json.dumps(available_words)
    })


def lobby(request, code):
    """Lobby page - waiting to start rounds"""
    game = get_object_or_404(Game, code=code)
    teams = game.teams.all()
    
    return render(request, 'timesup/lobby.html', {
        'game': game,
        'teams': teams
    })


def start_round(request, code, round_number):
    """Start a specific round"""
    game = get_object_or_404(Game, code=code)
    game.start_round(round_number)
    return redirect('timesup:play', code=game.code)


def play(request, code):
    """Main game play page"""
    game = get_object_or_404(Game, code=code)
    current_team = game.get_current_team()
    
    # Get remaining cards for this round
    remaining_cards = game.cards.filter(guessed_in_current_round=False)
    
    # Check if round is complete
    if not remaining_cards.exists() and game.status == 'playing':
        return redirect('timesup:round_complete', code=game.code)
    
    return render(request, 'timesup/play.html', {
        'game': game,
        'current_team': current_team,
        'remaining_cards': remaining_cards.count(),
        'total_cards': game.cards.count()
    })


def get_card(request, code):
    """API endpoint to get the next card"""
    game = get_object_or_404(Game, code=code)
    
    # Get excluded card IDs if provided (for passing or getting different cards)
    exclude_ids = request.GET.get('exclude', '')
    exclude_list = [id.strip() for id in exclude_ids.split(',') if id.strip()]
    
    # Get unguessed cards in shuffled order
    remaining_cards = game.cards.filter(guessed_in_current_round=False).order_by('round_order')
    
    remaining_list = list(remaining_cards)
    
    if not remaining_list:
        return JsonResponse({'complete': True})
    
    # Find the first card that's not in the exclude list
    card = None
    for c in remaining_list:
        if str(c.id) not in exclude_list:
            card = c
            break
    
    # If all cards are excluded (cycled through all), start over
    if not card:
        card = remaining_list[0]
    
    return JsonResponse({
        'id': card.id,
        'name': card.name,
        'remaining': len(remaining_list)
    })


@require_http_methods(["POST"])
def card_guessed(request, code):
    """Mark a card as guessed"""
    game = get_object_or_404(Game, code=code)
    data = json.loads(request.body)
    card_id = data.get('card_id')
    
    card = get_object_or_404(Card, id=card_id, game=game)
    card.guessed_in_current_round = True
    card.save()
    
    # Record the guess
    current_team = game.get_current_team()
    if current_team:
        GameRound.objects.create(
            game=game,
            team=current_team,
            round_number=game.current_round,
            card=card
        )
        current_team.add_score(game.current_round, 1)
    
    # Get next card in shuffled order
    remaining_cards = list(game.cards.filter(guessed_in_current_round=False).order_by('round_order'))
    
    if not remaining_cards:
        return JsonResponse({'complete': True, 'remaining': 0})
    
    next_card = remaining_cards[0]  # Get first card in the shuffled order
    return JsonResponse({
        'id': next_card.id,
        'name': next_card.name,
        'remaining': len(remaining_cards)
    })


@require_http_methods(["POST"])
def undo_card(request, code):
    """Undo the last guessed card"""
    game = get_object_or_404(Game, code=code)
    data = json.loads(request.body)
    card_id = data.get('card_id')
    
    card = get_object_or_404(Card, id=card_id, game=game)
    
    # Mark card as not guessed
    card.guessed_in_current_round = False
    card.save()
    
    # Remove the last game round entry for this card
    current_team = game.get_current_team()
    if current_team:
        last_round = GameRound.objects.filter(
            game=game,
            team=current_team,
            round_number=game.current_round,
            card=card
        ).last()
        
        if last_round:
            last_round.delete()
            # Subtract the score
            current_team.add_score(game.current_round, -1)
    
    # Count remaining cards
    remaining_count = game.cards.filter(guessed_in_current_round=False).count()
    
    return JsonResponse({
        'success': True,
        'remaining': remaining_count
    })


@require_http_methods(["POST"])
def end_turn(request, code):
    """End the current turn and move to next team"""
    game = get_object_or_404(Game, code=code)
    game.next_team()
    
    return JsonResponse({'success': True})


def round_complete(request, code):
    """Show round completion and scores"""
    game = get_object_or_404(Game, code=code)
    teams = game.teams.all()
    
    return render(request, 'timesup/round_complete.html', {
        'game': game,
        'teams': teams
    })


def final_scores(request, code):
    """Show final scores"""
    game = get_object_or_404(Game, code=code)
    game.status = 'finished'
    game.save()
    
    teams = game.teams.all().order_by('-score_round1', '-score_round2', '-score_round3')
    
    return render(request, 'timesup/final_scores.html', {
        'game': game,
        'teams': teams
    })
