from rest_framework import serializers
from .models import Memoria, MemoriaDetalle
from django.core.exceptions import ValidationError
from scheduling.common.serializer_fields import FlexibleDateTimeField
from rest_framework.reverse import reverse

class MemoriaSerializer(serializers.ModelSerializer):
    fecha_subida = FlexibleDateTimeField()
    imagen_display_name = serializers.SerializerMethodField(read_only=True)
    imagen_display_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Memoria
        fields = '__all__'
    
    def get_imagen_display_name(self, obj):
        if getattr(obj, 'imagen_display', None):
            return getattr(obj.imagen_display, 'name', None)
        return None

    def get_imagen_display_url(self, obj):
        # Intentar construir una URL absoluta si el storage lo permite y el request está en el contexto
        request = self.context.get('request') if hasattr(self, 'context') else None
        try:
            if getattr(obj, 'imagen_display', None) and hasattr(obj.imagen_display, 'url'):
                if request is not None:
                    return request.build_absolute_uri(obj.imagen_display.url)
                return obj.imagen_display.url
        except Exception:
            return None
        return None

    def to_representation(self, instance):
        """Personalizar la representación: eliminar el campo `loc_disco` bruto
        y dejar sólo metadatos/urls para archivos.
        """
        ret = super().to_representation(instance)
        # No exponer el FileField binario/raw
        ret.pop('loc_disco', None)
        return ret

    def validate_loc_disco(self, value):
        """Valida que el archivo sea un PDF."""
        if value and not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Solo se permiten archivos en formato PDF.")
        return value

class MemoriaDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoriaDetalle
        fields = '__all__'