from rest_framework import serializers

from oej.models import Position, StatusControl, Seat, Candidate


class CandidateExportSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='id')
    id_ine = serializers.CharField(source='id_ine')
    num_list = serializers.CharField(source='num_list')
    name = serializers.CharField(source='full_name')
    position_name = serializers.CharField(source='seat.position.short_name')
    circunscription_name = serializers.CharField(
        source='seat.judicial_district.short_name')

    class Meta:
        model = Candidate
        fields = [
            'id',
            'id_ine',
            'num_list',
            'name',
            'position_name',
            'circunscription_name',
        ]


class SeatExportSerializer(serializers.ModelSerializer):
    state = serializers.CharField(
        source='judicial_district.state.short_name')
    numero_jed = serializers.IntegerField(source='judicial_district.number')
    position_name = serializers.CharField(source='position.short_name')

    total_vacantes = serializers.CharField(source='total_offices')
    materia_index = serializers.IntegerField(source='topic_index')
    materia_name = serializers.CharField(source='topic.name')

    class Meta:
        model = Seat
        fields = [
            'id',
            'state',
            'numero_jed',
            'position_name',
            'materia_index',
            'materia_name',
            'total_vacantes',
            'real_mujeres',
            'real_hombres',
            'squares_mujeres',
            'squares_hombres',
            'probability_mujeres',
            'probability_hombres',
            'final_probability_mujeres',
            'final_probability_hombres',
            'circuit_probability_mujeres',
            'circuit_probability_hombres',
            'offices_mujeres',
            'offices_hombres',
            'shared_offices',
            'gender_forced',
            'forced_probability_mujeres',
            'forced_probability_hombres',
            'circuit_forced_probability_mujeres',
            'circuit_forced_probability_hombres',
            'selected_mujeres',
            'selected_hombres',
            'final_selected_mujeres',
            'final_selected_hombres',
            'circuit_selected_mujeres',
            'circuit_selected_hombres',
        ]
