from django.conf.global_settings import MIDDLEWARE_CLASSES
from settings_default import INSTALLED_APPS

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = 'please-generate-your-secret-key'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'sqlite.db',
    }
}

# FACEBOOK_APP_ID = ''
# FACEBOOK_API_SECRET = ''
# TUMBLR_CONSUMER_KEY = ''
# TUMBLR_CONSUMER_SECRET = ''
# TWITTER_CONSUMER_KEY = ''
# TWITTER_CONSUMER_SECRET = ''


MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INSTALLED_APPS += ('django_extensions', 'debug_toolbar')
INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel')
