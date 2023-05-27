# import_export_theunitedstatesio/admin.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.contrib import admin

from .models import TheUnitedStatesIoLegislatorCurrent


class LegislatorCurrentAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['first_name', 'last_name', 'bioguide_id', 'thomas_id', 'lis_id', 'govtrack_id',
                           'opensecrets_id', 'votesmart_id', 'cspan_id', 'wikipedia_id',
                           'ballotpedia_id', 'washington_post_id', 'icpsr_id', 'district',
                           'gender', 'birthday']}),
    ]
    list_display = ('id', 'first_name', 'last_name', 'bioguide_id')
    list_filter = ['last_name']
    search_fields = ['first_name']

admin.site.register(TheUnitedStatesIoLegislatorCurrent, LegislatorCurrentAdmin)

