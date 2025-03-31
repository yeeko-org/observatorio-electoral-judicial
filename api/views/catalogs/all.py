from django.utils.translation.trans_real import catalog
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions


from oej.models import (
    Position, StatusControl, Seat
)
from geo.models import Body, Power, Circunscription, State
from api.views.catalogs.serializers import (
    PositionSerializer, StatusControlSerializer, BodySerializer,
    PowerSerializer, CircunscriptionSerializer,
    StateSerializer, SeatSerializer
)



class CatalogsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        positions = Position.objects.all().prefetch_related("body")

        catalogs = {
            "position": PositionSerializer(positions, many=True).data,
            "seat": SeatSerializer(
                Seat.objects.all(), many=True).data,
            "status_control": StatusControlSerializer(
                StatusControl.objects.all(), many=True).data,
            "body": BodySerializer(
                Body.objects.all(), many=True).data,
            "power": PowerSerializer(
                Power.objects.all(), many=True).data,
            "circunscription": CircunscriptionSerializer(
                Circunscription.objects.all(), many=True).data,
            "state": StateSerializer(
                State.objects.all(), many=True).data,
        }
        return Response(catalogs)


