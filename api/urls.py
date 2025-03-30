from django.urls import include, path

from api.views.profile import CandidateViewSet, ProfessionalLicenseViewSet
from api.views.auth.login_views import UserLoginAPIView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'candidate', CandidateViewSet, basename='candidate')
router.register(r'professional_license',
                ProfessionalLicenseViewSet, basename='professional_license')


urlpatterns = [
    path('login/', UserLoginAPIView.as_view(), name='login'),
    path('catalogs/', include('api.views.catalogs.urls')),
    # path('space_time/', include('api.views.space_time.urls')),
    path('', include(router.urls)),
]
