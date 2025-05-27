from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404
from .models import Invite
import re


def index(request):
    fake_invite = {'name': ''}
    return render(request, 'party/invite_defense.html', {'invite': fake_invite, 'fake': True})

def new(request):
    if request.method == 'POST':
        name = request.POST.get('first_name', '').strip() + ' ' + request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone')
        phone_regex = r'^3\d{8,9}$' # Italian mobile phone regex
        if not re.match(phone_regex, phone):
            return render(request, 'party/create_invite.html', {'error': 'Invalid phone number format. Please enter a valid Italian mobile number.'})
        
        invite = Invite.objects.get_or_create(phone=phone)[0]
        invite.name = name
        invite.code = Invite.phone_to_base64(phone)
        
        try:
            invite.save()
            return redirect('invite', code=invite.code)
        except Exception as e:
            return render(request, 'party/create_invite.html', {'error': f'Error saving invite: {str(e)}'})
    return render(request, 'party/create_invite.html')

@csrf_exempt
def invite(request, code):    
    if request.method == 'POST':
        invite = get_object_or_404(Invite, code=code)
        invite.state = request.POST.get('attending')
        invite.save()
        return HttpResponse("ok")
    invite = get_object_or_404(Invite, code=code)
    if invite.foreign:
        return render(request, 'party/invite_defense_en.html', {'invite': invite}) 
    return render(request, 'party/invite_defense.html', {'invite': invite})

def from_phone(request, phone):
    invite = get_object_or_404(Invite, phone=int(phone))
    return redirect('invite', code=invite.code)

def list(request):
    invites = Invite.objects.all().order_by('name')
    stats = {
        'yes': invites.filter(state='YE').count(),
        'no': invites.filter(state='NO').count(),
        'pending': invites.filter(state='PD').count(),
        'plus': invites.filter(state='+1').count(),
        'total': invites.count(),
        'last_update': invites.order_by('-date_modified').first().date_modified.strftime('%d/%m/%Y %H:%M:%S') if invites.count() > 0 else 'N/A',
        'yes_percent': round(invites.filter(state='YE').count() / invites.count() * 100, 2) if invites.count() > 0 else 'N/A',
        'no_percent': round(invites.filter(state='NO').count() / invites.count() * 100, 2) if invites.count() > 0 else 'N/A',
        'pending_percent': round(invites.filter(state='PD').count() / invites.count() * 100, 2) if invites.count() > 0 else 'N/A',
        'plus_percent': round(invites.filter(state='+1').count() / invites.count() * 100, 2) if invites.count() > 0 else 'N/A',
    }
    
    if request.method == 'POST':
        if request.POST.get('filter') == 'sort_date':
            invites = invites.order_by('date_modified')
        elif request.POST.get('filter') == 'sort_name':
            invites = invites.order_by('name')
        elif request.POST.get('filter') == 'sort_state':
            invites = invites.order_by('state')
        elif request.POST.get('filter') == 'yes':
            invites = invites.filter(state='YE')
        elif request.POST.get('filter') == 'no':
            invites = invites.filter(state='NO')
        elif request.POST.get('filter') == 'pending':
            invites = invites.filter(state='PD')
        elif request.POST.get('filter') == 'plus':
            invites = invites.filter(state='+1')
        
    return render(request, 'party/list.html', {'invites': invites, 'stats': stats})

@csrf_exempt
def make_invite(request):
    if request.method == 'POST':
        invite = Invite()
        invite.name = request.POST.get('name')
        invite.phone = request.POST.get('phone')
        invite.phone_suffix = request.POST.get('suffix')
        invite.state = 'PD'
        invite.fuorisede = request.POST.get('fuorisede') == 'yes'
        invite.code = Invite.phone_to_base64(invite.phone)
        try:
            invite.save()
            return HttpResponse("ok")
        except Exception as e:
            return HttpResponse("error: " + str(e))
    return redirect('list')