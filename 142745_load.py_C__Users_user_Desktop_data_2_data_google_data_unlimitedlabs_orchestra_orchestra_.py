from django.apps import apps as django_apps
from django.conf import settings
from django.db import transaction

from orchestra.models import Certification
from orchestra.models import Workflow
from orchestra.models import Step
from orchestra.models import WorkflowVersion
from orchestra.workflow.defaults import get_default_assignment_policy
from orchestra.workflow.defaults import get_default_review_policy
from orchestra.workflow.directory import parse_workflow_directory
from orchestra.core.errors import WorkflowError


def get_workflow_version_slugs():
    versions = {}
    for app_name in settings.ORCHESTRA_WORKFLOWS:
        # App label is the last part of the app name by default
        app_label = app_name.split('.')[-1]
        workflow_directory = django_apps.get_app_config(app_label).path
        data = parse_workflow_directory(workflow_directory)
        workflow_slug = data['workflow']['slug']
        if versions.get(workflow_slug) is not None:
            raise WorkflowError('Workflow {} present in multiple apps: {}, {}'
                                .format(workflow_slug,
                                        versions[workflow_slug]['app_label'],
                                        app_label))
        else:
            versions[workflow_slug] = {
                'app_label': app_label,
                'versions': (version['slug'] for version in data['versions'])
            }
    return versions


@transaction.atomic
def load_workflow(app_label, version_slug, force=False):
    workflow_directory = django_apps.get_app_config(app_label).path
    data = parse_workflow_directory(workflow_directory)

    # Create the workflow object if it doesn't exist
    workflow_data = data['workflow']
    workflow, workflow_created = Workflow.objects.update_or_create(
        slug=workflow_data['slug'],
        defaults={
            'name': workflow_data['name'],
            'description': workflow_data['description'],
            'code_directory': workflow_directory,
            'sample_data_load_function': workflow_data.get(
                'sample_data_load_function')
        }
    )

    # Create all certifications for the workflow
    for certification_data in workflow_data['certifications']:
        Certification.objects.update_or_create(
            slug=certification_data['slug'],
            workflow=workflow,
            defaults={
                'name': certification_data['name'],
                'description': certification_data['description'],
            }
        )

    # Create the certification dependencies once all certs are in the db
    # Allow updating these over time so that a workflow's certifications can
    # evolve. This means that the user is responsible for ensuring that all
    # workers have the proper certifications after updating these dependencies.
    for certification_data in workflow_data['certifications']:
        certification = Certification.objects.get(
            slug=certification_data['slug'],
            workflow=workflow
        )
        required_certification_slugs = certification_data.get(
            'required_certifications', [])
        required_certifications = Certification.objects.filter(
            workflow=workflow,
            slug__in=required_certification_slugs
        )
        if required_certifications.count() != len(
                required_certification_slugs):
            raise WorkflowError(
                'Certification {} requires non-existent certification.'
                .format(certification_data['slug']))
        certification.required_certifications = list(required_certifications)

    # Load the desired versions
    desired_versions = [version_data for version_data in data['versions']
                        if version_data['slug'] == version_slug]
    if len(desired_versions) != 1:
        raise WorkflowError('Invalid version requested: {}'
                            .format(version_slug))
    load_workflow_version(desired_versions[0], workflow, force=force)


def load_workflow_version(version_data, workflow, force=False):
    # Create the version object
    version, version_created = WorkflowVersion.objects.update_or_create(
        slug=version_data['slug'],
        workflow=workflow,
        defaults={
            'name': version_data['name'],
            'description': version_data['description']
        }
    )

    if not version_created:
        if not force:
            # It is safe to error out after modifying the DB because
            # all of this code is wrapped in a transaction by load_workflow.
            raise WorkflowError('Version {} already exists'
                                .format(version_data['slug']))

        # Check that the versions are safe to merge
        new_step_slugs = set(step['slug'] for step in version_data['steps'])
        old_step_slugs = set(
            Step.objects
            .filter(workflow_version=version)
            .values_list('slug', flat=True)
        )
        if new_step_slugs != old_step_slugs:
            raise WorkflowError('Even with --force, cannot change the steps '
                                'of a workflow. Drop and recreate the '
                                'database to reset, or create a new version '
                                'for your workflow.')

    # Create or update the version steps.
    old_creation_dependencies = {}
    old_submission_dependencies = {}
    for step_data in version_data['steps']:
        is_human = step_data.get('is_human', True)
        step, step_created = Step.objects.update_or_create(
            slug=step_data['slug'],
            workflow_version=version,
            defaults={
                'name': step_data['name'],
                'description': step_data['description'],
                'is_human': is_human,
                'execution_function': step_data.get('execution_function', {}),
                'assignment_policy': step_data.get(
                    'assignment_policy',
                    get_default_assignment_policy(is_human)),
                'review_policy': step_data.get(
                    'review_policy',
                    get_default_review_policy(is_human)),
                'user_interface': step_data.get('user_interface', {}),
            }
        )
        if not step_created:
            old_creation_dependencies[step_data['slug']] = set(
                step.creation_depends_on.values_list('slug', flat=True))
            old_submission_dependencies[step_data['slug']] = set(
                step.submission_depends_on.values_list('slug', flat=True))

        # Don't prevent updates to these, because we want to allow
        # certifications to evolve over the lifetime of a workflow.
        _set_step_dependencies(step, step_data, 'required_certifications',
                               Certification, workflow=workflow)

    # Set up step dependencies once the steps objects are in the DB.
    for step_data in version_data['steps']:
        step_slug = step_data['slug']
        step = Step.objects.get(
            slug=step_slug,
            workflow_version=version
        )

        # Set step creation dependencies.
        _verify_dependencies_not_updated(
            step_data,
            'creation_depends_on',
            old_creation_dependencies.get(step_slug)
        )
        _set_step_dependencies(step, step_data, 'creation_depends_on', Step,
                               workflow_version=version)

        # Set step submission dependencies.
        _verify_dependencies_not_updated(
            step_data,
            'submission_depends_on',
            old_submission_dependencies.get(step_slug)
        )
        _set_step_dependencies(step, step_data, 'submission_depends_on', Step,
                               workflow_version=version)


def _verify_dependencies_not_updated(step_data, dependency_attr,
                                     old_dependencies):
    new_dependencies = set(step_data.get(dependency_attr, []))
    if old_dependencies is not None and old_dependencies != new_dependencies:
        raise WorkflowError(
            'Even with --force, cannot change the topology of a workflow. '
            'Drop and recreate the database to reset, or create a new '
            'version for your workflow.')


def _set_step_dependencies(step, step_data, dependency_attr, dependency_model,
                           **model_filters):
    dependency_slugs = set(step_data.get(dependency_attr, []))
    dependencies = list(dependency_model.objects.filter(
        slug__in=dependency_slugs, **model_filters))
    if len(dependencies) != len(dependency_slugs):
        raise WorkflowError(
            '{}.{} contains a non-existent slug.'
            .format(step_data['slug'], dependency_attr))
    setattr(step, dependency_attr, dependencies)
