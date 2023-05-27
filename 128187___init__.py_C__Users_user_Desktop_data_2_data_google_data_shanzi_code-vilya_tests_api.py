from vilya.api import create_app
from tests import VilyaAppTestCase

class VilyaApiTestCase(VilyaAppTestCase):
    
    def _create_app(self, settings):
        return create_app(settings)
