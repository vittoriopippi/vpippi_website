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
    
    # Check which rounds have been completed
    completed_rounds = set()
    for round_num in [1, 2, 3]:
        # A round is completed if all cards were guessed in that round
        round_records = GameRound.objects.filter(game=game, round_number=round_num)
        if round_records.exists():
            # Check if all cards have been guessed in this round
            total_cards = game.cards.count()
            guessed_in_round = round_records.values('card').distinct().count()
            if guessed_in_round >= total_cards:
                completed_rounds.add(round_num)
    
    return render(request, 'timesup/lobby.html', {
        'game': game,
        'teams': teams,
        'completed_rounds': completed_rounds
    })


def start_round(request, code, round_number):
    """Start a specific round"""
    game = get_object_or_404(Game, code=code)

    if round_number not in (1, 2, 3):
        return redirect('timesup:lobby', code=game.code)

    # If this round already has guesses recorded, do not allow restarting it via URL.
    # Restarting would reset card flags but keep scores/records, inflating points beyond deck size.
    if GameRound.objects.filter(game=game, round_number=round_number).exists():
        return redirect('timesup:lobby', code=game.code)

    # If the round is already in progress, just continue playing.
    if game.status == 'playing' and game.current_round == round_number:
        return redirect('timesup:play', code=game.code)

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
    """API endpoint to get the next card or all remaining cards"""
    game = get_object_or_404(Game, code=code)
    
    # Check if requesting all cards
    if request.GET.get('all') == 'true':
        # Get excluded card ID if provided
        exclude_id = request.GET.get('exclude', '')
        
        # Get all unguessed cards in shuffled order
        remaining_cards = game.cards.filter(guessed_in_current_round=False).order_by('round_order')
        
        if exclude_id:
            remaining_cards = remaining_cards.exclude(id=exclude_id)
        
        remaining_list = list(remaining_cards)
        
        if not remaining_list:
            return JsonResponse({'complete': True})
        
        # Return all cards
        cards_data = [{'id': c.id, 'name': c.name} for c in remaining_list]
        return JsonResponse({
            'cards': cards_data,
            'complete': False
        })
    
    # Original single card logic (kept for backwards compatibility)
    exclude_ids = request.GET.get('exclude', '')
    exclude_list = [id.strip() for id in exclude_ids.split(',') if id.strip()]
    
    remaining_cards = game.cards.filter(guessed_in_current_round=False).order_by('round_order')
    remaining_list = list(remaining_cards)
    
    if not remaining_list:
        return JsonResponse({'complete': True})
    
    card = None
    for c in remaining_list:
        if str(c.id) not in exclude_list:
            card = c
            break
    
    if not card:
        card = remaining_list[0]
    
    return JsonResponse({
        'id': card.id,
        'name': card.name,
        'remaining': len(remaining_list)
    })


@require_http_methods(["POST"])
def card_guessed(request, code):
    """Mark a card as guessed (legacy endpoint - kept for compatibility)"""
    game = get_object_or_404(Game, code=code)
    data = json.loads(request.body)
    card_id = data.get('card_id')
    
    card = get_object_or_404(Card, id=card_id, game=game)
    if not card.guessed_in_current_round:
        card.guessed_in_current_round = True
        card.save()
    
    # Record the guess
    current_team = game.get_current_team()
    if current_team and not GameRound.objects.filter(
        game=game,
        round_number=game.current_round,
        card=card,
    ).exists():
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
    
    next_card = remaining_cards[0]
    return JsonResponse({
        'id': next_card.id,
        'name': next_card.name,
        'remaining': len(remaining_cards)
    })


@require_http_methods(["POST"])
def submit_turn(request, code):
    """Submit all guessed cards from a turn at once"""
    game = get_object_or_404(Game, code=code)
    data = json.loads(request.body)
    guessed_card_ids = data.get('guessed_card_ids', [])
    
    current_team = game.get_current_team()
    
    # Mark all cards as guessed and record scores
    for card_id in guessed_card_ids:
        try:
            card = Card.objects.get(id=card_id, game=game)
            
            # Only process if not already guessed (prevent duplicates)
            if not card.guessed_in_current_round:
                card.guessed_in_current_round = True
                card.save()
                
                # Record the guess
                if current_team and not GameRound.objects.filter(
                    game=game,
                    round_number=game.current_round,
                    card=card,
                ).exists():
                    GameRound.objects.create(
                        game=game,
                        team=current_team,
                        round_number=game.current_round,
                        card=card
                    )
                    current_team.add_score(game.current_round, 1)
        except Card.DoesNotExist:
            continue
    
    # Check if round is complete
    remaining_cards = game.cards.filter(guessed_in_current_round=False).count()
    
    return JsonResponse({
        'success': True,
        'remaining': remaining_cards,
        'complete': remaining_cards == 0
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
