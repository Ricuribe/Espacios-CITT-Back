from rest_framework import serializers
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