from rest_framework import serializers

from oej.models import Position, StatusControl, Seat


class SeatExportSerializer(serializers.ModelSerializer):
    state = serializers.CharField(
        source='judicial_district.state.short_name')
    circuit = serializers.IntegerField(source='judicial_district.number')
    position_name = serializers.CharField(source='position.short_name')
    topic = serializers.CharField(source='topic.name')

    class Meta:
        model = Seat
        fields = [
            'id',
            'judicial_district',
            'state',
            'circuit',
            'position',
            'position_name',
            'total_offices',
            'squares_mujeres',
            'squares_hombres',
            'plus_squares',
            'real_mujeres',
            'real_hombres',
            'probability_mujeres',
            'probability_hombres',
            'offices_mujeres',
            'offices_hombres',
            'gender_forced',
            'shared_offices',
            'topic',
            'topic_index',
            'selected_mujeres',
            'selected_hombres',
            'final_selected_mujeres',
            'final_selected_hombres',
        ]

