from django_filters import (
    FilterSet, DateFilter, CharFilter, BooleanFilter, NumberFilter)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, permissions
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from api.pagination import CustomPagination
from api.permissions import IsFullEditorOrReadOnly

from api.views.action_file import ActionFileMixin
from rest_framework.filters import SearchFilter, OrderingFilter

from oej.models import Candidate, ProfessionalLicense, Biography

from api.views.profile.serializers import (
    CandidateSerializer, CandidateFullSerializer, CandidatePublicSerializer,
    ProfessionalLicenseSerializer, BiographySerializer)



class CandidateFilter(FilterSet):

    # status_register = CharFilter(field_name='status_register__name')
    # has_files = BooleanFilter(
    #     field_name='files', lookup_expr='isnull', exclude=True)
    position = NumberFilter(
        field_name='seat__position_id', lookup_expr='exact')
    circunscription = NumberFilter(
        field_name='seat__circunscription_id', lookup_expr='exact')
    own_profiles = BooleanFilter(method='filter_own_profiles')

    def filter_own_profiles(self, queryset, name, value):
        from django.db.models import Q
        if value:
            user = self.request.user
            return queryset.filter(
                Q(user_register=user) | Q(user_validation=user)
            )
        return queryset

    class Meta:
        model = Candidate
        fields = {
            'sex': ['exact'],
            'user_register': ['exact'],
            'user_validation': ['exact'],
        }


class CandidateViewSet(ActionFileMixin, viewsets.ModelViewSet):
    permission_classes = [IsFullEditorOrReadOnly]
    queryset = Candidate.objects.all()\
        .select_related('seat')\
        .prefetch_related('licenses')

    pagination_class = CustomPagination

    filterset_class = CandidateFilter

    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
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
            'list': CandidatePublicSerializer,
            'retrieve': CandidatePublicSerializer,
            'create': CandidateFullSerializer,
            'update': CandidateFullSerializer,
        }
        if self.request.user.is_authenticated and self.request.user.is_staff:
            action_serializer['list'] = CandidateSerializer
            action_serializer['retrieve'] = CandidateFullSerializer
        return action_serializer.get(self.action, self.serializer_class)

    def create(self, request, *args, **kwargs):
        data = request.data
        data['editor'] = request.user.id
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def generate_summary(self, request, pk=None):
        from oej.sonar.sonar_research import SonarResearch
        candidate = self.get_object()
        fields = {
            "full_name_normalized": "Nombre",
            "professional_text": "Detalles de la experiencia profesional",
            "academic_text": "Complemento de experiencia académica",
            "other_text": "Otros detalles como conflictos de interés y otros hallazgos:",
        }
        user_prompt = ""
        for field, label in fields.items():
            if field in request.data:
                user_prompt += f"{label}:\n\n {request.data[field]}\n\n"
        req_data = request.data
        print("user_prompt", user_prompt)
        sonar = SonarResearch(ai_company='openai', engine='gpt-4o-2024-11-20')
        sonar.build_prompt("oej/sonar/summary_prompt.txt")
        result = sonar.send_prompt(user_prompt)
        # result = "HOLA"
        return Response(result, status=200)

    # def update(self, request, *args, **kwargs):
    #     data = request.data
    #     if request.user.is_full_editor:
    #         data['reviewer'] = request.user.id
    #     return super().update(request, *args, **kwargs)


class ProfessionalLicenseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsFullEditorOrReadOnly]
    queryset = ProfessionalLicense.objects.all()
    serializer_class = ProfessionalLicenseSerializer

