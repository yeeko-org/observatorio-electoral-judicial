from rest_framework import routers
from django.urls import path, include

from .views import GossipResponseViewSet

router = routers.DefaultRouter()

router.register(r'response', GossipResponseViewSet)

urlpatterns = (
    path('', include(router.urls)),
)


