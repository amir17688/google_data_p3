#-*- coding: utf-8 -*-

__author__ = "rotoudjimaye"

from django.conf import settings
from django.utils.importlib import import_module

import logging
logger = logging.getLogger('djangojy.jyquartz')

QUARTZ_AVAILABLE = True
try:
    from org.quartz import JobBuilder, TriggerBuilder, CronScheduleBuilder
    from org.rt.jyquartz import ScheduledJob
    from org.rt.modjy.servlet import ModjyServlet

    SCHEDULER = ModjyServlet.SCHEDULER
    FN_CACHE = {}
except:
    QUARTZ_AVAILABLE = False

if QUARTZ_AVAILABLE:
    for app in settings.INSTALLED_APPS:
        try:
            jytask = import_module(app+".jytasks")
            logger.info("::JyQuartz: deploying file jytasks.py in installed application %s ", app)
        except ImportError, e:
            logger.debug("::JyQuartz: No scheduled jytasks found in installed application %s ", app, exc_info=True)
            pass
    logger.info("::Started jyQuartz django application successfuly...")