from __future__ import unicode_literals

from django.forms import model_to_dict
from django.utils import six
from rest_framework.authtoken.models import Token

from nodeconductor.core.log import event_logger
from nodeconductor.core.models import StateMixin


def create_auth_token(sender, instance, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


def preserve_fields_before_update(sender, instance, **kwargs):
    if instance.pk is None:
        return

    meta = instance._meta
    old_instance = meta.model._default_manager.get(pk=instance.pk)

    excluded_fields = [field.name for field in meta.many_to_many]
    excluded_fields.append(meta.pk.name)
    old_values = model_to_dict(old_instance, exclude=excluded_fields)

    setattr(instance, '_old_values', old_values)


def delete_error_message(sender, instance, name, source, target, **kwargs):
    """ Delete error message if instance state changed from erred """
    if source != StateMixin.States.ERRED:
        return
    instance.error_message = ''
    instance.save(update_fields=['error_message'])


def log_user_save(sender, instance, created=False, **kwargs):
    if created:
        event_logger.user.info(
            'User {affected_user_username} has been created.',
            event_type='user_creation_succeeded',
            event_context={'affected_user': instance})
    else:
        old_values = instance._old_values

        password_changed = instance.password != old_values['password']
        activation_changed = instance.is_active != old_values['is_active']
        user_updated = any(
            old_value != getattr(instance, field_name)
            for field_name, old_value in six.iteritems(old_values)
            if field_name not in ('password', 'is_active', 'last_login')
        )

        if password_changed:
            event_logger.user.info(
                'Password has been changed for user {affected_user_username}.',
                event_type='user_password_updated',
                event_context={'affected_user': instance})

        if activation_changed:
            if instance.is_active:
                event_logger.user.info(
                    'User {affected_user_username} has been activated.',
                    event_type='user_activated',
                    event_context={'affected_user': instance})
            else:
                event_logger.user.info(
                    'User {affected_user_username} has been deactivated.',
                    event_type='user_deactivated',
                    event_context={'affected_user': instance})

        if user_updated:
            event_logger.user.info(
                'User {affected_user_username} has been updated.',
                event_type='user_update_succeeded',
                event_context={'affected_user': instance})


def log_user_delete(sender, instance, **kwargs):
    event_logger.user.info(
        'User {affected_user_username} has been deleted.',
        event_type='user_deletion_succeeded',
        event_context={'affected_user': instance})


def log_ssh_key_save(sender, instance, created=False, **kwargs):
    if created:
        event_logger.sshkey.info(
            'SSH key {ssh_key_name} has been created.',
            event_type='ssh_key_creation_succeeded',
            event_context={'ssh_key': instance})


def log_ssh_key_delete(sender, instance, **kwargs):
    event_logger.sshkey.info(
        'SSH key {ssh_key_name} has been deleted.',
        event_type='ssh_key_deletion_succeeded',
        event_context={'ssh_key': instance})
