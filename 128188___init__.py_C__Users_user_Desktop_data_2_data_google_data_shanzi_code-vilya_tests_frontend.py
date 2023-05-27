from vilya.frontend import create_app
from tests import VilyaAppTestCase

class VilyaFrontendTestCase(VilyaAppTestCase):
    
    def _create_app(self, settings):
        return create_app(settings)
