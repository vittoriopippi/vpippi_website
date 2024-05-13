from django.shortcuts import render, redirect
import csv
import os
from django.http import JsonResponse, HttpResponse
from django.core.files import File
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from user_study.models import Competitor, Prompt, SampleImage, Player, Answer, Question
from itertools import combinations
from pathlib import Path
import random
from datetime import timedelta, datetime
from django.conf import settings
import pandas as pd

QUESTIONS_PER_PLAYER = 60
QUESTIONS_PER_PAIR = 60

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
    return render(request, 'main/login.html', {'avg_time': avg_time})

def index(request):
    player_id = request.session.get('player_id')
    if player_id is None or not Player.objects.filter(pk=player_id).exists():
        return redirect('login')

    player = Player.objects.get(pk=player_id)
    answered_questions = Answer.objects.all().filter(player=player, question__is_control=False).count() 
    if answered_questions >= QUESTIONS_PER_PLAYER:
        player.finished = True
        player.save()
        return redirect('login')
    
    if player.finished:
        return redirect('login')

    control_questions = Question.objects.all().filter(is_control=True).order_by('pk')
    control_questions_answered = Answer.objects.all().filter(player=player, question__is_control=True)
    for question in control_questions_answered:
        control_questions = control_questions.exclude(pk=question.question.pk)
    control_questions = list(control_questions)

    other_questions = list(Question.objects.all().filter(is_control=False))
    random.shuffle(other_questions)
    questions = control_questions + other_questions[:QUESTIONS_PER_PLAYER - answered_questions]

    first_question = questions[0]
    context = {
        'player': player,
        'first_question': first_question,
        'questions': questions,
        'total_questions': len(control_questions) + QUESTIONS_PER_PLAYER,
        'answered_questions': answered_questions,
        }
    return render(request, 'main/index.html', context)

def scoreboard(request):
    players = Player.objects.all().filter(visible=True, finished=True).order_by('-accuracy')
    context = {
        'players': players,
        }
    return render(request, 'main/scoreboard.html', context)

@csrf_exempt
def post_answer(request):
    if request.POST:
        player_id = request.POST['player_id']
        if player_id is None or not Player.objects.filter(pk=player_id).exists():
            return HttpResponse('ERROR')
        player = Player.objects.get(pk=player_id)
        question_id = request.POST['question_id']
        if question_id is None or not Question.objects.filter(pk=question_id).exists():
            return HttpResponse('ERROR')
        question = Question.objects.get(pk=request.POST['question_id'])
        winner = question.sample_a if request.POST['answer'] == 'img_a' else question.sample_b
        Answer.objects.create(player=player, winner=winner, question=question)
        player.update_accuracy()
        player.update_correct_control_answers()

        answered_questions = Answer.objects.all().filter(player=player, question__is_control=False).count() 
        remaining_questions = QUESTIONS_PER_PLAYER - answered_questions
        if remaining_questions == 0:
            player.finished = True
            player.save()
        return JsonResponse({'status': 'OK', 'remaining_questions': remaining_questions})
    return HttpResponse('ERROR')

@staff_member_required
def import_images(request):
    # Competitor.objects.all().delete()
    
    if os.name == 'nt':
        root = Path(r'D:\Work\Projects\BugUserStudy\images_jpg')
    else:
        root = Path('/home/vpippi/BugUserStudy/images')

    for img_path in root.rglob('*'):
        if not img_path.is_file() and not img_path.suffix in ('.png', '.jpg'):
            continue
        competitor_name = img_path.parent.parent.name
        prompt_text = img_path.parent.name.replace('_', ' ')
        competitor, _ = Competitor.objects.get_or_create(name=competitor_name)
        prompt, _ = Prompt.objects.get_or_create(eng_text=prompt_text)
        with img_path.open(mode='rb') as f:
            SampleImage.objects.create(competitor=competitor, prompt=prompt, img=File(f, name=img_path.name))
    return HttpResponse(f'Imported {len(SampleImage.objects.all())} images')

@staff_member_required 
def generate_questions(request):
    # Question.objects.all().filter(is_control=False).delete()
    competitors = Competitor.objects.all().filter(available=True)

    lcm_competitors = [c for c in competitors if c.name.startswith('lcm')]
    other_competitors = [c for c in competitors if not c.name.startswith('lcm')]

    prompts = Prompt.objects.all()
    for competitors in (lcm_competitors, other_competitors):
        for competitor_a, competitor_b in combinations(competitors, 2):
            for prompt in prompts:
                for _ in range(QUESTIONS_PER_PAIR):
                    sample_a = SampleImage.objects.all().filter(competitor=competitor_a, prompt=prompt, exclude_from_study=False).order_by("?").first()
                    sample_b = SampleImage.objects.all().filter(competitor=competitor_b, prompt=prompt, exclude_from_study=False).order_by("?").first()
                    sample_a, sample_b = (sample_a, sample_b) if random.random() > 0.5 else (sample_b, sample_a)
                    Question.objects.create(sample_a=sample_a, sample_b=sample_b, is_control=False)
    return HttpResponse(f'Generated {len(Question.objects.all())} questions')

@staff_member_required 
def delete_questions(request):
    Question.objects.all().delete()
    return HttpResponse('Deleted all questions')

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
    delete_questions(request)
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

    good_players = Player.objects.all().filter(correct_control_answers__gte=5)
    answers = Answer.objects.all().filter(player__in=good_players)
    data = answers.values('player__name', 'question__is_control', 'question__sample_a__competitor__name', 'question__sample_b__competitor__name', 'question__sample_a__prompt__eng_text', 'winner__competitor__name')
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
    prompts = Prompt.objects.all()
    prompt_dicts = [prompt.answer_count_by_competitor() for prompt in prompts]
    prompt_values = [list(prompt_value.values()) for prompt_value in prompt_dicts]
    prompt_competitors = [list(prompt_value.keys()) for prompt_value in prompt_dicts]
    prompt_total = [sum(prompt_value.values()) for prompt_value in prompt_dicts]
    prompt_values_perc = [[round(value / total * 100, 2) for value in prompt_value] for prompt_value, total in zip(prompt_values, prompt_total)]

    total_values = [sum(prompt_value) for prompt_value in zip(*prompt_values)]
    total_values_perc = [sum(prompt_value) / len(prompt_values_perc) for prompt_value in zip(*prompt_values_perc)]
    total_competitors = prompt_competitors[0]

    prompts_data = list(zip(list(prompts), [list(zip(*a))for a in list(zip(prompt_values, prompt_values_perc, prompt_competitors))]))
    context = {
        'prompts_data': prompts_data,
        'total_data': list(zip(total_values, total_values_perc, total_competitors)),
        }
    return render(request, 'main/stats.html', context)
