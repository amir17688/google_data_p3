from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, FormView
from django.views.generic.list import ListView
from django.utils.translation import ugettext as _

from project.access_control_views import LoginRequiredView, UserPrivateView


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')


class UserDetails(LoginRequiredView, DetailView):

    model = get_user_model()
    slug_field = 'username'


class UserEdit(UserPrivateView, UpdateView):

    model = get_user_model()
    slug_field = 'username'
    fields = ['email']


class UserChangePassword(LoginRequiredView, FormView):
    form_class = PasswordChangeForm
    template_name = 'auth/password_change_form.html'

    def get_success_url(self):
        return reverse('user', kwargs={'slug': self.kwargs['slug']})

    def get_form_kwargs(self):
        kwargs = super(UserChangePassword, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Password changed.'))
        return super(UserChangePassword, self).form_valid(form)
