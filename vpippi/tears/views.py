from django.shortcuts import render, redirect
from .models import User, Day, Tears
from datetime import datetime

ITA_MONTHS = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
              'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
ITA_MONTHS_DICT = {m:i+1 for i, m in enumerate(ITA_MONTHS)}

def index(request, username=None):
    days = Day.objects.all().order_by('-date')
    if username is not None:
        user, created = User.objects.get_or_create(name=username)
        days = days.filter(user__name=user.name)

    context = {'days': days, 'username': username}
    return render(request, "tears/index.html", context)

def create(request, username):
    if request.method == "POST":
        day = int(request.POST["day"])
        month = ITA_MONTHS_DICT[request.POST["month"]]
        day_description = request.POST["day_desc"]
        tears_description = request.POST["tears_desc"]

        day_status = None
        if 'day_happy' in request.POST:
            day_status = 'h'
        elif 'day_sad' in request.POST:
            day_status = 's'
        elif 'day_bored' in request.POST:
            day_status = 'b'

        tears_qta = 0
        if 'tears_qta_1' in request.POST:
            tears_qta = 1
        elif 'tears_qta_2' in request.POST:
            tears_qta = 2
        elif 'tears_qta_3' in request.POST:
            tears_qta = 3

        tears_status = None
        if 'tears_happy' in request.POST:
            tears_status = 'h'
        elif 'tears_sad' in request.POST:
            tears_status = 's'
        elif 'tears_bored' in request.POST:
            tears_status = 'b'

        user, created = User.objects.get_or_create(name=username)
        day, created = Day.objects.get_or_create(user=user, date=datetime(datetime.now().year, month, day))
        if day_status != None:
            day.status = day_status 
            day.description = day_description if day_description != "" else day.description
        if tears_qta > 0 and tears_status != None:
            tears = Tears.objects.create(status=tears_status, quantity=tears_qta, description=tears_description)
            day.tears.add(tears)
        day.save()
        return redirect("tears_index", username=username)

    context = {
        'dates': list(range(1, 32)),
        'curr_date': datetime.now().day,
        'months': ITA_MONTHS,
        'curr_month': ITA_MONTHS[datetime.now().month - 1],
        'username': username,
    }
    return render(request, "tears/create.html", context)