from django.shortcuts import render, redirect
import csv
import os
from django.http import JsonResponse, HttpResponse
from django.core.files import File
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from user_study_emuru.models import Competitor, SampleImage, Player, Answer, Skipped
from itertools import combinations
from pathlib import Path
import random
from datetime import timedelta, datetime
from django.conf import settings
import pandas as pd

QUESTIONS_PER_PLAYER = 48

def login(request):
    if request.POST:
        entered_username = request.POST['username']
        if entered_username is None or len(entered_username) == 0:
            return redirect('login')
        player = Player.objects.create(name=entered_username)
        request.session['player_id'] = player.pk
        return redirect('index')

    times = []
    for player in Player.objects.all().filter(visible=True):
        time_elps = player.time_delta()
        if time_elps is not None and player.finished:
            times.append(time_elps.total_seconds())
    avg_time = sorted(times)[len(times) // 2] if len(times) > 0 else 'N/A'
    if avg_time != 'N/A':
        avg_time = str(timedelta(seconds=avg_time)).split('.')[0][2:]
    return render(request, 'user_study_emuru/login.html', {'avg_time': avg_time})

def index(request):
    player_id = request.session.get('player_id')
    if player_id is None or not Player.objects.filter(pk=player_id).exists():
        return redirect('login')

    player = Player.objects.get(pk=player_id)
    answered_questions = Answer.objects.all().filter(player=player).count() + Skipped.objects.filter(player=player).count()
    if answered_questions >= QUESTIONS_PER_PLAYER:
        player.finished = True
        player.save()
        return redirect('login')
    
    if player.finished:
        return redirect('login')

    # Get all SampleImages that are references and the payer didn't aswer yet
    answers = Answer.objects.all().filter(player=player)
    shtg_keys = {answer.winner.shtg_key for answer in answers}
    references = SampleImage.objects.filter(competitor__reference=True).order_by('?')
    references = [ref for ref in references if ref.shtg_key not in shtg_keys]
    competitors = [SampleImage.objects.filter(competitor__reference=False, shtg_key=ref.shtg_key).order_by('?') for ref in references]
    
    context = {
        'player': player,
        'first_reference': references[0],
        'first_competitors': competitors[0],
        'references': references,
        'competitors': competitors,
        'total_questions': QUESTIONS_PER_PLAYER,
        'answered_questions': answered_questions,
        }
    return render(request, 'user_study_emuru/index.html', context)

def scoreboard(request):
    players = Player.objects.all().filter(visible=True, finished=True).order_by('-accuracy')
    context = {
        'players': players,
        }
    return render(request, 'user_study_emuru/scoreboard.html', context)

@csrf_exempt
def post_answer(request):
    if request.POST:
        player_id = request.POST['player_id']
        if player_id is None or not Player.objects.filter(pk=player_id).exists():
            return HttpResponse('ERROR')
        player = Player.objects.get(pk=player_id)
        if request.POST['answer'].startswith('skip'):
            shtg_key = request.POST['answer'].split('_')[1]
            Skipped.objects.create(player=player, shtg_key=shtg_key)
        else:
            winner = SampleImage.objects.get(pk=int(request.POST['answer']))
            Answer.objects.create(player=player, winner=winner)
        player.update_accuracy()
        player.update_correct_control_answers()

        answered_questions = Answer.objects.all().filter(player=player).count() + Skipped.objects.filter(player=player).count()
        remaining_questions = QUESTIONS_PER_PLAYER - answered_questions
        if remaining_questions == 0:
            player.finished = True
            player.save()
        return JsonResponse({'status': 'OK', 'remaining_questions': remaining_questions})
    return HttpResponse('ERROR')

@csrf_exempt
def upload_question(request):
    if request.method == 'POST':
        for competitor_name, image in request.FILES.items():
            competitor, _ = Competitor.objects.get_or_create(name=competitor_name)
            # Check if a SampleImage with the same shtg_key already exists
            if not SampleImage.objects.filter(competitor=competitor, shtg_key=image.name).exists():
                with image.open() as f:
                    name = f'{image.name}.png'
                    SampleImage.objects.create(
                        competitor=competitor,
                        dataset='_'.join(image.name.split('_')[:2]),
                        img=File(f, name=name),
                        shtg_key=image.name
                    )
        return JsonResponse({'status': 'OK'})
    return HttpResponse(f'Not implemented the method {request.method}', status=405)


@staff_member_required 
def delete_competitors(request):
    Competitor.objects.all().delete()
    return HttpResponse('Deleted all competitors')

@staff_member_required
def delete_all(request):
    Answer.objects.all().delete()
    Player.objects.all().delete()
    SampleImage.objects.all().delete()
    Player.objects.all().delete()
    delete_competitors(request)
    return HttpResponse('Deleted all answers, players, questions and competitors')

@staff_member_required 
def dump_answers(request):
    now = datetime.now()
    now_str = now.strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="dump_{now_str}.csv"'},
    )

    answers = Answer.objects.all()
    data = answers.values('date', 'player__name', 'winner__competitor__name', 'winner__shtg_key')
    df = pd.DataFrame(data)
    df.to_csv(path_or_buf=response)
    return response

@staff_member_required
def update_players(request):
    for player in Player.objects.all():
        player.update_accuracy()
        player.update_correct_control_answers()
    return redirect('scoreboard')

def stats(request):
    # 1. Get all relevant competitors
    competitors = Competitor.objects.filter(available=True, reference=False)

    # 2. Calculate the total number of answers per competitor (existing logic)
    answers = [
        Answer.objects.filter(winner__competitor=competitor).count()
        for competitor in competitors
    ]
    total_answers = sum(answers)
    perc = [
        (answer / total_answers) * 100 if total_answers else 0
        for answer in answers
    ]
    
    # 3. For dataset-specific stats, get all distinct dataset names
    datasets = SampleImage.objects.values_list('dataset', flat=True).distinct()

    dataset_competitors = []
    for dataset in datasets:
        # All answers that belong to this dataset
        dataset_answers = Answer.objects.filter(winner__dataset=dataset)
        total_dataset_answers = dataset_answers.count()

        competitor_data = []
        for competitor in competitors:
            c_count = dataset_answers.filter(winner__competitor=competitor).count()
            c_perc = (c_count / total_dataset_answers) * 100 if total_dataset_answers else 0
            competitor_data.append((competitor.name, c_count, c_perc))

        # Save each dataset's name, competitor data, and total answers for display
        dataset_competitors.append((dataset, competitor_data, total_dataset_answers))

    context = {
        'competitors': zip(competitors, answers, perc),
        'total_answers': total_answers,
        'dataset_competitors': dataset_competitors,
    }
    return render(request, 'user_study_emuru/stats.html', context)
