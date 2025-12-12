from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserPreferenceViewSet, UserKnowledgeViewSet, OrderViewSet, cocina_panel

router = DefaultRouter()
router.register(r'preferences', UserPreferenceViewSet)
router.register(r'knowledge', UserKnowledgeViewSet)
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),              # API REST
    path('cocina_panel/', cocina_panel, name='cocina_panel'),  # Panel web
]
