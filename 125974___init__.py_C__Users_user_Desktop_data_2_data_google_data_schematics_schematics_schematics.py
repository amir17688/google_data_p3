# -*- coding: utf-8 -*-

__version__ = '2.0.0.dev2'

from .models import Model, ModelMeta

types.compound.Model = Model
types.compound.ModelMeta = ModelMeta

__all__ = ['Model']

