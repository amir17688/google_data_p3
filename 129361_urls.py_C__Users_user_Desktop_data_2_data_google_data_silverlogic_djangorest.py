from rest_framework import routers

from .views import MenuItemViewSet, MenuItemOptionViewSet


router = routers.SimpleRouter()

router.register('menu-items', MenuItemViewSet)
router.register('menu-item-options', MenuItemOptionViewSet)

urlpatterns = router.urls
