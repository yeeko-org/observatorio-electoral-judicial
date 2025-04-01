from rest_framework import serializers

from oej.models import (
    Candidate, ProfessionalLicense, Biography, Seat, Position)
from geo.models import Body, Power, Circunscription


class ProfessionalLicenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProfessionalLicense
        fields = '__all__'


class ProfessionalLicensePublicSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProfessionalLicense
        fields = ['id_licence', 'level', 'career', 'institution', 'year']


class BiographySerializer(serializers.ModelSerializer):

    class Meta:
        model = Biography
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


class CandidateSerializer(serializers.ModelSerializer):
    licenses = ProfessionalLicensePublicSerializer(many=True, read_only=True)
    position = serializers.IntegerField(source='seat.position_id')

    class Meta:
        model = Candidate
        fields = '__all__'


class CandidatePublicSerializer(serializers.ModelSerializer):
    licenses = ProfessionalLicensePublicSerializer(many=True, read_only=True)
    position = serializers.IntegerField(source='seat.position_id')

    class Meta:
        model = Candidate
        fields = [
            'id', 'id_ine', 'full_name_normalized', 'full_name', 'seat',
            'first_year', 'sex', 'powers',
            'ine_photo', 'num_list', 'ine_cv', 'photo_small', 'photo',
            'academic_text', 'professional_text', 'professional_summary',
            'more_info_text', 'ine_data',
            'sources', 'licenses', 'position'
        ]


class CandidatePublicFullSerializer(CandidatePublicSerializer):

    class Meta:
        model = Candidate
        fields = [
            'id', 'id_ine', 'full_name_normalized', 'full_name', 'seat',
            'first_year', 'sex', 'powers',
            'ine_photo', 'num_list', 'ine_cv', 'photo_small', 'photo',
            'academic_text', 'professional_text', 'professional_summary',
            'more_info_text', 'ine_data',
            'sources', 'licenses', 'position'
        ]


class CandidateFullSerializer(serializers.ModelSerializer):
    biography_full = BiographySerializer(read_only=True, source='biography')
    licenses = ProfessionalLicenseSerializer(many=True, read_only=True)
    powers_full = PowerSerializer(many=True, read_only=True, source='powers')
    seat_full = SeatFullSerializer(read_only=True, source='seat')
    position = serializers.IntegerField(source='seat.position_id')

    class Meta:
        model = Candidate
        fields = '__all__'
        read_only_fields = ['photo', 'photo_small']

