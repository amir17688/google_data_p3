from __future__ import unicode_literals

import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from appconf import AppConf


class SystemJSConf(AppConf):
    # Main switch
    ENABLED = not settings.DEBUG

    # Path to JSPM executable. Must be on the path, or a full path
    JSPM_EXECUTABLE = 'jspm'

    OUTPUT_DIR = 'SYSTEMJS'

    PACKAGE_JSON_DIR = getattr(settings, 'BASE_DIR', None)

    DEFAULT_JS_EXTENSIONS = True

    class Meta:
        prefix = 'systemjs'

    def configure_package_json_dir(self, value):
        if value is None:
            raise ImproperlyConfigured(
                "Tried auto-guessing the location of 'package.json', "
                "but settings.BASE_DIR does not exist. Either set BASE_DIR "
                "or SYSTEMJS_PACKAGE_JSON_DIR"
            )
        return os.path.abspath(value)
