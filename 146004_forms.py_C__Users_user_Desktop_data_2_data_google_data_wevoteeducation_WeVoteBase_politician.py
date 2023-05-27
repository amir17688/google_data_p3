# politician/forms.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-
# See Django Cookbook, chapter 3, p. 57

from django import forms
from django.utils.translation import ugettext_lazy as _, ugettext
from django.contrib.auth.models import User

from crispy_forms.helper import FormHelper
from crispy_forms import layout, bootstrap

from politician.models import Politician, PoliticianTagLink
from tag.models import Tag


class TagNewForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['hashtag_text']

    def __init__(self, *args, **kwargs):
        super(TagNewForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_action = ""
        self.helper.form_method = "POST"

        self.helper.layout = layout.Layout(
            # layout.Fieldset(
            #     _("Main data"),
            #     layout.Field("hashtag_text", css_class="input-block-level"),
            # ),
            layout.Field("hashtag_text", css_class="input-block-level"),

            bootstrap.FormActions(
                layout.Submit('submit', _('Save')),
            )
        )


# class TagNewProcessForm(forms.Form):
#     politician = forms.ModelChoiceField
#     new_tag = forms.CharField(
#         label=_("New Tag Label"),
#         queryset=Tag.object.all(),
#         required=True,
#     )
#
#     def __init__(self, request, *args, **kwargs):
#         super(TagNewProcessForm, self).__init__(*args, **kwargs)
#         self.request = request
#         self.fields['new_tag'].queryset = self.fields['new_tag'].queryset.exclude()