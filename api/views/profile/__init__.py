from django_filters import (
    FilterSet, DateFilter, CharFilter, BooleanFilter, NumberFilter)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, permissions
from rest_framework.viewsets import GenericViewSet

from api.pagination import CustomPagination

from api.views.action_file import ActionFileMixin
from rest_framework.filters import SearchFilter, OrderingFilter

from oej.models import Candidate, ProfessionalLicense, Biography

from api.views.profile.serializers import (
    CandidateSerializer, CandidateFullSerializer,
    ProfessionalLicenseSerializer, BiographySerializer)



class CandidateFilter(FilterSet):

    # status_register = CharFilter(field_name='status_register__name')
    # has_files = BooleanFilter(
    #     field_name='files', lookup_expr='isnull', exclude=True)
    position = NumberFilter(
        field_name='seat__position_id', lookup_expr='exact')

    class Meta:
        model = Candidate
        fields = {
            # 'source': ['exact'],
            # 'editor': ['exact'],
            # 'reviewer': ['exact'],
        }


class CandidateViewSet(ActionFileMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Candidate.objects.all()

    pagination_class = CustomPagination

    filterset_class = CandidateFilter

    filter_backends = [OrderingFilter, DjangoFilterBackend]
    # filter_backends = [
    #     OrderingAutoFilter, DjangoFilterBackend, UnaccentSearchFilter]
    search_fields = ["full_name_normalized"]
    ordering_fields = ['full_name_normalized', 'seat_id']
    # ordering_fields = ['__auto__']
    ordering = ['id']
    serializer_class = CandidateSerializer
    action_add_file_param = 'photo'

    def get_queryset(self):
        is_retrieve = self.action == 'retrieve'
        queryset = super().get_queryset()
        queryset = self.queryset\
            .select_related('biography', 'seat', 'seat__position')\
            .prefetch_related('licenses', 'powers'
        ) if is_retrieve else queryset
        return queryset

    def get_serializer_class(self):
        action_serializer = {
            'retrieve': CandidateFullSerializer,
            'create': CandidateFullSerializer,
            'update': CandidateFullSerializer,
            # 'add_file': NoteFileSerializer,
            # 'patch': NoteCreateSerializer,
        }
        return action_serializer.get(self.action, self.serializer_class)

    def create(self, request, *args, **kwargs):
        data = request.data
        data['editor'] = request.user.id
        return super().create(request, *args, **kwargs)

    # def update(self, request, *args, **kwargs):
    #     data = request.data
    #     if request.user.is_full_editor:
    #         data['reviewer'] = request.user.id
    #     return super().update(request, *args, **kwargs)


class ProfessionalLicenseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = ProfessionalLicense.objects.all()
    serializer_class = ProfessionalLicenseSerializer

