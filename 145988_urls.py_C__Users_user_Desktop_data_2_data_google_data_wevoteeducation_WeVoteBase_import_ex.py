# import_export/urls.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.import_export_index, name='import_export_index'),
    url(r'^transfer_from_google_civic/', views.import_export_transfer_google_civic_to_local_tables_view,
        name='transfer_from_google_civic'),
    url(r'^transfer_from_maplight/', views.transfer_maplight_data_to_we_vote_tables,
        name='transfer_from_maplight'),
    url(r'^transfer_from_theunitedstatesio/', views.import_export_transfer_theunitedstatesio_to_local_tables_view,
        name='transfer_from_theunitedstatesio'),
    # url(r'^position_json/', views.ExportPositionDataToJson, name='position_json'),
    url(r'^candidate_campaigns/', views.ExportCandidateCampaignDataToJson.as_view(), name='candidate_campaigns'),
    url(r'^organizations/', views.ExportOrganizationDataToJson.as_view(), name='organizations'),
    url(r'^positions/', views.ExportPositionDataToJson.as_view(), name='positions'),

    # # When we manually add linkages between politicians coming from one system and another,
    # # we want to be able to export so we can share with other projects
    # url(r'^politician_name_mapping_export/', views.ExportPoliticianNameMappingDataToJson.as_view(),
    #     name='politician_name_mapping_export'),
    # # Once exported, we can manually place this json file in /import_export/import_data

    url(r'^update_all_id_we_vote/', views.update_all_id_we_vote, name='update_all_id_we_vote'),
    url(r'^import_sample_positions/', views.import_we_vote_sample_positions_data_from_json,
        name='import_sample_positions'),
]
