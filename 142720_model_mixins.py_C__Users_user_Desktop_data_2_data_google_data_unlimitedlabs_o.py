from django.db.models import Q

from orchestra.core.errors import ModelSaveError


class WorkflowMixin(object):

    def __str__(self):
        return self.slug


class WorkflowVersionMixin(object):

    def __str__(self):
        return '{} - {}'.format(self.workflow.slug, self.slug)


class CertificationMixin(object):

    def __str__(self):
        return '{} - {}'.format(self.slug, self.workflow.slug)


class StepMixin(object):

    def __str__(self):
        return '{} - {} - {}'.format(self.slug, self.workflow_version.slug,
                                     self.workflow_version.workflow.slug)


class WorkerMixin(object):

    def __str__(self):
        return '{} - @{} -{}'.format(
            self.user.username,
            self.slack_username,
            self.phone
        )


class WorkerCertificationMixin(object):

    def __str__(self):
        return '{} - {} - {} - {} - {}'.format(
            self.worker.user.username, self.certification.slug,
            self.certification.workflow.slug,
            dict(self.TASK_CLASS_CHOICES)[self.task_class],
            dict(self.ROLE_CHOICES)[self.role])

    def save(self, *args, **kwargs):
        if self.role == self.Role.REVIEWER:
            if not (type(self).objects
                    .filter(worker=self.worker, task_class=self.task_class,
                            certification=self.certification,
                            role=self.Role.ENTRY_LEVEL)
                    .exists()):
                raise ModelSaveError('You are trying to add a reviewer '
                                     'certification ({}) for a worker without '
                                     'an entry-level certification'
                                     .format(self))
        super().save(*args, **kwargs)


class ProjectMixin(object):

    def __str__(self):
        return '{} ({})'.format(str(self.workflow_version.slug),
                                self.short_description)


class TaskMixin(object):

    def __str__(self):
        return '{} - {}'.format(str(self.project), str(self.step.slug))


class TaskAssignmentMixin(object):

    def save(self, *args, **kwargs):
        if self.task.step.is_human:
            if self.worker is None:
                raise ModelSaveError('Worker has to be present '
                                     'if worker type is Human')
        else:
            if self.worker is not None:
                raise ModelSaveError('Worker should not be assigned '
                                     'if worker type is Machine')

        super().save(*args, **kwargs)

    def __str__(self):
        return '{} - {} - {}'.format(
            str(self.task), self.assignment_counter, str(self.worker))


class PayRateMixin(object):

    def __str__(self):
        return '{} ({} - {})'.format(
            self.worker, self.start_date, self.end_date or 'now')

    def save(self, *args, **kwargs):
        if self.end_date and self.end_date < self.start_date:
            raise ModelSaveError('end_date must be greater than '
                                 'start_date')

        if self.end_date is None:
            # If end_date is None, need to check that no other PayRates have
            # end_date is None, nor do they overlap.
            if type(self).objects.exclude(id=self.id).filter(
                    (Q(end_date__gte=self.start_date) |
                     Q(end_date__isnull=True)),
                    worker=self.worker).exists():
                raise ModelSaveError(
                    'Date range overlaps with existing PayRate entry')
        else:
            # If end_date is not None, need to check if other PayRates overlap.
            if (type(self).objects.exclude(id=self.id).filter(
                    start_date__lte=self.end_date,
                    end_date__isnull=True,
                    worker=self.worker).exists() or
                type(self).objects.exclude(id=self.id).filter(
                    (Q(start_date__lte=self.end_date) &
                     Q(end_date__gte=self.start_date)),
                    worker=self.worker).exists()):
                raise ModelSaveError(
                    'Date range overlaps with existing PayRate entry')
        super().save(*args, **kwargs)
