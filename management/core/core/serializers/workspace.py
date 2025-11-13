from rest_framework import serializers
from ..models.workspace import Workspace, WorkspaceResource, Table


class WorkspaceResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceResource
        fields = '__all__'


class WorkspaceSerializer(serializers.ModelSerializer):
    zone_space_display = serializers.CharField(source='get_zone_space_display', read_only=True)
    class Meta:
        model = Workspace
        fields = '__all__'
        db_table = 'espacios'

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None