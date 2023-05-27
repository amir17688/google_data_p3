from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, UpdateView
from apps.profiles.forms import ProfileForm
from apps.profiles.models import City, Profile


class ProfileList(ListView):
    template_name = 'profiles/list.html'
    model = Profile

    def get_queryset(self):
        city_id = self.request.GET.get('city', False)
        if city_id:
            return self.model.objects.filter(city__id=city_id)
        return super(ProfileList, self).get_queryset()

    def get_context_data(self, **kwargs):
        context = super(ProfileList, self).get_context_data(**kwargs)
        context.update({
            'cities': City.objects.all()
        })

        return context


class ProfileDetail(DetailView):
    template_name = 'profiles/detail.html'
    model = Profile

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        user = get_object_or_404(self.model, user__username=username)

        return user


class ProfileEdit(UpdateView):
    template_name = 'profiles/form.html'
    form_class = ProfileForm
    model = Profile

    def get_object(self):
        return self.model.objects.get(
            user__username=self.request.user.username)

    def get_success_url(self):
        return reverse('profile_detail', args=[self.request.user.username])

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileEdit, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.save()

        return super(ProfileEdit, self).form_valid(form)
