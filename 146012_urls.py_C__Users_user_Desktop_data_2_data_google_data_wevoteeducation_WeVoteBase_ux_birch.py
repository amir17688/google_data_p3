# ux_birch/urls.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.conf.urls import url

from ux_birch import views

urlpatterns = [
    url(r'^$', views.my_ballot_view, name='my_ballot'),
    url(r'^start/', views.start_view, name='start'),
    url(r'^ask/(?P<candidate_campaign_id>[0-9]+)/$', views.ask_view, name='ask'),
]
