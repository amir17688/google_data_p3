from django.contrib import admin
from apps.profiles.models import Profile, City


class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(City, CityAdmin)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city')
admin.site.register(Profile, ProfileAdmin)
