# import_export_theunitedstatesio/urls.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.import_voting_info_project_from_xml_view, name='import_voting_info_project_from_xml_view'),
    # url(r'^(?P<pk>[0-9]+)/$', views.LegislatorCurrentDetailView.as_view(), name='legislatorcurrent_detail'),
]
