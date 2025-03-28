from django.urls import include, path
from rest_framework import routers

from api.views.catalogs.all import CatalogsView

router = routers.DefaultRouter()


urlpatterns = [
    path("all/", CatalogsView.as_view(), name="catalogs_all"),
    path('', include(router.urls)),
]
