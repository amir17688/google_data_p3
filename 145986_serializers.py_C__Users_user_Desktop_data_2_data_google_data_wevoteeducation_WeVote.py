# import_export/serializers.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-
from election_office_measure.models import CandidateCampaign
from organization.models import Organization
from position.models import PositionEntered
from rest_framework import serializers


class CandidateCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateCampaign
        fields = ('id_we_vote', 'candidate_name', 'candidate_url', 'email', 'facebook_url', 'google_civic_election_id',
                  'google_plus_url', 'order_on_ballot', 'party', 'phone', 'photo_url', 'twitter_url', 'youtube_url')


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id_we_vote', 'name', 'url')


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PositionEntered
        fields = ('id_we_vote', 'organization_id_we_vote', 'candidate_campaign_id_we_vote',
                  'measure_campaign_id_we_vote', 'date_entered', 'election_id', 'stance', 'more_info_url',
                  'statement_text', 'statement_html')
