from rest_framework import serializers
from ..models.event import Event, EventDetail, RejectReason, EventSpace
from .common import FlexibleDateTimeField


class EventSerializer(serializers.ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    start_datetime = FlexibleDateTimeField()
    end_datetime = FlexibleDateTimeField()
    create_invitation = serializers.BooleanField(write_only=True, default=False)

    class Meta:
        model = Event
        fields = [
            'id_event', 
            'title',
            'start_datetime',
            'end_datetime',
            'created_by',
            'created_by_username',
            'form_public_link',
            'form_edit_link',
            'create_invitation'
        ]
        read_only_fields = ['form_public_link', 'form_edit_link']

class EventDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventDetail
        fields = '__all__'

class RejectReasonSerializer(serializers.ModelSerializer):

    class Meta:
        model = RejectReason
        fields = '__all__'

class EventSpaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventSpace
        fields = '__all__'