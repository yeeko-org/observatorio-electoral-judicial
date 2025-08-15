from rest_framework import serializers

from oej.models import Position, StatusControl, Seat, Candidate


class SeatExportSerializer(serializers.ModelSerializer):
    seat_id = serializers.IntegerField(source='id')
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
            'seat_id',
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
            'offices_mujeres',
            'offices_hombres',
            'shared_offices',
            'null_votes_hombres',
            'null_votes_mujeres',
            'voted_people',
            'nominal_list',
            'probability_mujeres',
            'probability_hombres',
            'final_probability_mujeres',
            'final_probability_hombres',
            'circuit_probability_mujeres',
            'circuit_probability_hombres',
            # 'gender_forced',
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


class CandidateExportSerializer(serializers.ModelSerializer):
    candidate_id = serializers.IntegerField(source='id')
    seat = SeatExportSerializer()
    powers = serializers.SerializerMethodField()

    def get_powers(self, obj):
        key_powers = [power.key_name for power in obj.powers.all()]
        return ", ".join(key_powers)

    class Meta:
        model = Candidate
        fields = [
            'candidate_id',
            'id_ine',
            'num_list',
            'full_name',
            'sex',
            'powers',
            'final_votes',
            'real_winner',
            'real_winner_final',
            'real_winner_circuit',
            'probability',
            'final_probability',
            'circuit_probability',
            'anomaly',
            'final_anomaly',
            'circuit_anomaly',
            'seat',
        ]


class SeatNalExportSerializer(serializers.ModelSerializer):
    seat_id = serializers.IntegerField(source='id')
    circunscription = serializers.SerializerMethodField()
    position_name = serializers.CharField(source='position.short_name')
    total_vacantes = serializers.CharField(source='total_offices')

    def get_circunscription(self, obj):
        if obj.circunscription:
            return obj.circunscription.number
        return ''

    class Meta:
        model = Seat
        fields = [
            'seat_id',
            'circunscription',
            'position_name',
            'total_vacantes',
            'real_mujeres',
            'real_hombres',
            'squares_mujeres',
            'squares_hombres',
        ]


class CandidateNalExportSerializer(serializers.ModelSerializer):
    candidate_id = serializers.IntegerField(source='id')
    seat = SeatNalExportSerializer()
    powers = serializers.SerializerMethodField()

    def get_powers(self, obj):
        key_powers = [power.key_name for power in obj.powers.all()]
        return ", ".join(key_powers)

    class Meta:
        model = Candidate
        fields = [
            'candidate_id',
            'id_ine',
            'num_list',
            'full_name',
            'sex',
            'powers',
            'final_votes',
            'real_winner',
            'seat',
            'total_ads',
            'spend_lower',
            'spend_upper',
        ]

