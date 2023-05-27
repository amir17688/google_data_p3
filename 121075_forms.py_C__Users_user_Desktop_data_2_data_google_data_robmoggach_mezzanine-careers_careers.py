from django import forms

from careers.models import JobPost


hidden_field_defaults = ("status", "gen_description")


class JobPostForm(forms.ModelForm):
    """
    Model form for ``JobPost`` that provides the quick job post panel in the
    admin dashboard.
    """

    class Meta:
        model = JobPost
        fields = ("title", "content") + hidden_field_defaults

    def __init__(self):
        initial = {}
        for field in hidden_field_defaults:
            initial[field] = JobPost._meta.get_field(field).default
        super(JobPostForm, self).__init__(initial=initial)
        for field in hidden_field_defaults:
            self.fields[field].widget = forms.HiddenInput()
