from scaffold.settings import *

SESSION_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 2592000 #30 days
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_FRAME_DENY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True

SECURE_REDIRECT_EXEMPT = [
    # App Engine doesn't use HTTPS internally, so the /_ah/.* URLs need to be exempt.
    # djangosecure compares these to request.path.lstrip("/"), hence the lack of preceding /
    r"^_ah/"
]

SECURE_CHECKS += ["scaffold.checks.check_csp_sources_not_unsafe"]

DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = False

# Remove unsafe-inline from CSP_STYLE_SRC. It's there in default to allow
# Django error pages in DEBUG mode render necessary styles
if "'unsafe-inline'" in CSP_STYLE_SRC:
    CSP_STYLE_SRC = list(CSP_STYLE_SRC)
    CSP_STYLE_SRC.remove("'unsafe-inline'")
    CSP_STYLE_SRC = tuple(CSP_STYLE_SRC)
