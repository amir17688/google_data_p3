# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-02 01:22
from __future__ import unicode_literals

import uuid

import django.db.models.deletion
import jsonfield.fields
from django.conf import settings
from django.db import migrations, models

import openslides.utils.models


def add_default_projector(apps, schema_editor):
    """
    Adds default projector and activates clock.
    """
    # We get the model from the versioned app registry;
    # if we directly import it, it will be the wrong version.
    Projector = apps.get_model('core', 'Projector')
    projector_config = {}
    projector_config[uuid.uuid4().hex] = {
        'name': 'core/clock',
        'stable': True}
    # We use bulk_create here because we do not want model's save() method
    # to be called because we do not want our autoupdate signals to be
    # triggered.
    Projector.objects.bulk_create([Projector(config=projector_config)])


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mediafiles', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'default_permissions': (),
                'permissions': (('can_use_chat', 'Can use the chat'),),
            },
            bases=(openslides.utils.models.RESTModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ConfigStore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=255, unique=True)),
                ('value', jsonfield.fields.JSONField()),
            ],
            options={
                'default_permissions': (),
                'permissions': (('can_manage_config', 'Can manage configuration'),),
            },
        ),
        migrations.CreateModel(
            name='CustomSlide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256)),
                ('text', models.TextField(blank=True)),
                ('weight', models.IntegerField(default=0)),
                ('attachments', models.ManyToManyField(blank=True, to='mediafiles.Mediafile')),
            ],
            options={
                'default_permissions': (),
                'ordering': ('weight', 'title'),
            },
            bases=(openslides.utils.models.RESTModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Projector',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('config', jsonfield.fields.JSONField()),
                ('scale', models.IntegerField(default=0)),
                ('scroll', models.IntegerField(default=0)),
            ],
            options={
                'default_permissions': (),
                'permissions': (
                    ('can_see_projector', 'Can see the projector'),
                    ('can_manage_projector', 'Can manage the projector'),
                    ('can_see_frontpage', 'Can see the front page')),
            },
            bases=(openslides.utils.models.RESTModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'default_permissions': (),
                'permissions': (('can_manage_tags', 'Can manage tags'),),
                'ordering': ('name',),
            },
            bases=(openslides.utils.models.RESTModelMixin, models.Model),
        ),
        migrations.RunPython(add_default_projector),
    ]