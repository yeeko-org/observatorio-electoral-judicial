from rest_framework import serializers

from oej.models import (
    Position, StatusControl, Seat
)
from geo.models import Body, Power, Circunscription, State


class BodySerializer(serializers.ModelSerializer):
    class Meta:
        model = Body
        fields = '__all__'


class PositionSerializer(serializers.ModelSerializer):
    body_full = BodySerializer(read_only=True)
    class Meta:
        model = Position
        fields = '__all__'


class StatusControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusControl
        fields = '__all__'


class PowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Power
        fields = '__all__'


class CircunscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circunscription
        fields = '__all__'


class StateSerializer(serializers.ModelSerializer):

    class Meta:
        model = State
        fields = '__all__'


class SeatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Seat
        fields = '__all__'



