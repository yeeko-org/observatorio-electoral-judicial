from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from gossip.models import GossipResponse, ResponseFile
from gossip.api.serializers import GossipResponseSerializer, ResponseFileSerializer
from rest_framework.permissions import BasePermission


class IsAdminOrCreator(BasePermission):

    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        if request.method in ['POST']:
            return True
        return False


class ActionFileMixin(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrCreator]
    action_add_file_param: str = ""

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def add_file(self, request, pk=None):
        object = self.get_object()
        request.data['gossip_response'] = object.id
        file_serializer = ResponseFileSerializer(data=request.data)

        file_serializer.is_valid(raise_exception=True)
        file_serializer.save(**{'gossip_response': object})

        return Response(file_serializer.data, status=201)


class GossipResponseViewSet(ActionFileMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminOrCreator]
    queryset = GossipResponse.objects.all()

    serializer_class = GossipResponseSerializer


class NoteFileViewSet(mixins.DestroyModelMixin):
    queryset = ResponseFile.objects.all()
    serializer_class = ResponseFileSerializer
    permission_classes = [IsAdminOrCreator]




