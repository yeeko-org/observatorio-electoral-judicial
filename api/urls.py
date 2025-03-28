from django.urls import include, path

# from api.views.profile import NoteViewSet, NoteFileViewSet
from api.views.auth.login_views import UserLoginAPIView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# router.register(r'note', NoteViewSet, basename='note')


urlpatterns = [
    path('login/', UserLoginAPIView.as_view(), name='login'),
    path('catalogs/', include('api.views.catalogs.urls')),
    # path('space_time/', include('api.views.space_time.urls')),
    path('', include(router.urls)),
]
