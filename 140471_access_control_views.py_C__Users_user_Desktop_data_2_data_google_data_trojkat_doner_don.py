from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.shortcuts import render

from .models import Project, Ticket, Log


class LoginRequiredView(View):
    '''
    This view can be visited only by authenticated users.
    '''

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredView, self).dispatch(*args, **kwargs)


class UserPrivateView(View):
    '''
    This view can be visited only by single user (view owner).
    '''

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        if not self.request.user == self.get_object():
            return render(self.request, 'access-denied.html')

        return super(UserPrivateView, self).dispatch(*args, **kwargs)


class SuperUserView(View):
    '''
    This view can be visited only by superusers.
    '''

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        if not self.request.user.is_superuser:
            return render(self.request, 'access-denied.html')

        return super(SuperUserView, self).dispatch(*args, **kwargs)


class ProjectReletedView(View):

    url_pk_related_model = Project
    project = None

    def get_project(self):
        '''
        Based on self.url_pk_related_model get project instance and set it as self.project.
        '''
        if self.project:
            # project is already available
            return

        model_instance = self.url_pk_related_model.objects.get(pk=self.kwargs['pk'])

        if isinstance(model_instance, Project):
            self.project = model_instance
        elif isinstance(model_instance, Ticket):
            self.project = model_instance.project
        elif isinstance(model_instance, Log):
            self.project = model_instance.ticket.project
        else:
            raise ValueError

    def is_project_member(self):
        self.get_project()
        return self.request.user.is_superuser or self.request.user in self.project.members.all()


class ProjectView(ProjectReletedView):
    '''
    If project IS PRIVATE give access to:
        - project members
        - superusers
    '''

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        self.get_project()
        if self.project.is_private and not self.is_project_member():
            return render(self.request, 'access-denied.html')

        return super(ProjectView, self).dispatch(*args, **kwargs)


class MembersOnlyView(ProjectReletedView):
    '''
    This view can be visited only by:
        - project members
        - superusers
    '''

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        if not self.is_project_member():
            return render(self.request, 'access-denied.html')

        return super(MembersOnlyView, self).dispatch(*args, **kwargs)
