# -*- coding: utf-8 -*-

__author__ = 'rotoudjimaye'

from django.contrib import admin
from models import *


admin.site.register(OutboxSm)
#admin.site.register(InboxSm)

