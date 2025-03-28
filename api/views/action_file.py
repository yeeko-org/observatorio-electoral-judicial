from typing import TYPE_CHECKING

from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response


if TYPE_CHECKING:
    from rest_framework.viewsets import ModelViewSet
else:
    class ModelViewSet:
        pass


class ActionFileMixin(ModelViewSet):
    action_add_file_param: str = ""

    @action(detail=True, methods=['post'],
            parser_classes=[MultiPartParser, FormParser])
    def add_file(self, request, pk=None):
        object = self.get_object()
        file_serializer = self.get_serializer(data=request.data)

        file_serializer.is_valid(raise_exception=True)
        file_serializer.save(**{self.action_add_file_param: object})

        return Response(file_serializer.data, status=201)
