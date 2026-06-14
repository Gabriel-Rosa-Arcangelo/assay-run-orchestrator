from rest_framework.routers import DefaultRouter

from .views import AssayRunViewSet, QcMetricViewSet

router = DefaultRouter()
router.register("runs", AssayRunViewSet, basename="run")
router.register("qc-metrics", QcMetricViewSet, basename="qc-metric")

urlpatterns = router.urls
