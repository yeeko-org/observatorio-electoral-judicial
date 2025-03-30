from rest_framework import serializers

from oej.models import (
    Candidate, ProfessionalLicense, Biography, Seat, Position)
from geo.models import Body, Power, Circunscription


class ProfessionalLicenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProfessionalLicense
        fields = '__all__'


class BiographySerializer(serializers.ModelSerializer):

    class Meta:
        model = Biography
        fields = '__all__'


class CandidateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Candidate
        fields = '__all__'


class PowerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Power
        fields = '__all__'


class PositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Position
        fields = '__all__'


class SeatFullSerializer(serializers.ModelSerializer):
    position_full = PositionSerializer(read_only=True, source='position')

    class Meta:
        model = Seat
        fields = '__all__'


class CandidateFullSerializer(serializers.ModelSerializer):
    biography = BiographySerializer(read_only=True)
    licenses = ProfessionalLicenseSerializer(
        many=True, read_only=True)
    powers_full = PowerSerializer(many=True, read_only=True, source='powers')
    seat_full = SeatFullSerializer(read_only=True, source='seat')

    class Meta:
        model = Candidate
        fields = '__all__'

