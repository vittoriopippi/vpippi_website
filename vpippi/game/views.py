from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Map, Interaction, Door, Player


def index(request):
    return redirect('load_map', map_name='university')

def load_map(request, map_name):
    map = get_object_or_404(Map, name=map_name)
    player = Player.objects.get(name='vittorio')
    context = {
        'map': map,
        'player': player,
        'x': map.origin_x,
        'y': map.origin_y,
        'orientation': map.origin_orientation,
        }
    return render(request, 'game/index.html', context)