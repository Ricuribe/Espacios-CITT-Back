from rest_framework import serializers
from .models import Memoria, MemoriaDetalle
from django.core.exceptions import ValidationError
from rest_framework.reverse import reverse
from django.utils import timezone


class FlexibleDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        # Al enviar al frontend, convertimos a la zona horaria del proyecto y quitamos el sufijo
        if value is None:
            return None
        if timezone.is_aware(value):
            # Convertimos a la zona horaria del proyecto
            value = timezone.localtime(value)
        return value.strftime('%Y-%m-%dT%H:%M:%S')

    def to_internal_value(self, value):
        # Al recibir del frontend, añadimos la zona horaria del proyecto
        if value is None:
            return None
        if isinstance(value, str) and not any(x in value for x in ['+', '-', 'Z']):
            # Si no tiene zona horaria, asumimos que está en la zona horaria del proyecto
            value = f"{value}{timezone.get_current_timezone_name()}"
        return super().to_internal_value(value)

class MemoriaSerializer(serializers.ModelSerializer):
    fecha_subida = FlexibleDateTimeField()
    imagen_display_name = serializers.SerializerMethodField(read_only=True)
    imagen_display_url = serializers.SerializerMethodField(read_only=True)
    created_at = FlexibleDateTimeField(read_only=True)
    updated_at = FlexibleDateTimeField(read_only=True)
    
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