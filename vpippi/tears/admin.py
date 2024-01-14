from django.contrib import admin
from .models import User, Tears, Day


class DayAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'status', 'description')
    ordering = ('-date',)
    list_filter = ('date', 'status')

class TearsAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'quantity', 'description')
    ordering = ('-quantity',)
    list_filter = ('status', 'quantity')

    @admin.display(description='user')
    def user(self, obj):
        return Day.objects.filter(tears=obj).first().user

class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'days_count', 'tears_count')
    ordering = ('name',)

    @admin.display(description='days count')
    def days_count(self, obj):
        return Day.objects.filter(user=obj).count()

    @admin.display(description='tears count')
    def tears_count(self, obj):
        return Tears.objects.filter(day__user=obj).count()

admin.site.register(User, UserAdmin)
admin.site.register(Tears, TearsAdmin)
admin.site.register(Day, DayAdmin)
