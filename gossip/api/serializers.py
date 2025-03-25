from rest_framework import serializers
from gossip.models import GossipResponse, ResponseFile


class ResponseFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseFile
        fields = '__all__'


class GossipResponseSerializer(serializers.ModelSerializer):
    files = ResponseFileSerializer(many=True, read_only=True)

    class Meta:
        model = GossipResponse
        fields = '__all__'
