import os
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Memoria, MemoriaDetalle
from django.forms.models import model_to_dict
from .serializers import MemoriaSerializer
from django.db.models import Q
from datetime import datetime
from django.core.exceptions import ValidationError
from .filter_config import get_valid_fields, get_career_choices, get_escuela_choices, get_detalle_valid_fields
from .models import validar_rut


class DownloadMemoryView(APIView):
    """
    Endpoint para descargar archivos PDF de memorias.
    """

    def get(self, request, pk):
        try:
            memory = Memoria.objects.get(pk=pk)
        except Memoria.DoesNotExist:
            return Response({"error": "La memoria solicitada no existe."}, status=status.HTTP_404_NOT_FOUND)

        if not memory.loc_disco:
            return Response({"error": "No hay archivo disponible para esta memoria."}, status=status.HTTP_404_NOT_FOUND)

        file_path = memory.loc_disco.path
        if not os.path.exists(file_path):
            return Response({"error": "El archivo no se encuentra en el servidor."}, status=status.HTTP_404_NOT_FOUND)

        # Devuelve el archivo PDF como descarga
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
    
class MemoryDetailView(APIView):
    """
    Endpoint que devuelve los datos de una memoria específica y sus detalles relacionados.
    (Se excluye el campo `loc_disco` ya que se obtiene desde el endpoint de descarga).
    """
    def get(self, request, pk):
        try:
            memory = Memoria.objects.get(pk=pk)
        except Memoria.DoesNotExist:
            return Response({"error": "La memoria solicitada no existe."}, status=status.HTTP_404_NOT_FOUND)

        # Usar el serializer de DRF para representar la instancia principal.
        # Evitamos incluir `loc_disco` (archivo PDF) en la respuesta y
        # añadimos una URL pública para la imagen si existe.
        try:
            serializer = MemoriaSerializer(memory, context={'request': request})
            memory_data = serializer.data
        except Exception:
            # Fallback si el serializer falla por alguna razón
            try:
                memory_data = model_to_dict(memory, exclude=['loc_disco', 'imagen_display'])
            except Exception:
                memory_data = {"id": memory.pk}

        # Recolectar relaciones "detalles" (one-to-many y many-to-many)
        details = {}
        for field in memory._meta.get_fields():
            if not (field.one_to_many or field.many_to_many):
                continue

            # Intentar obtener el manager relacionado por accessor_name (reverse) o por name (direct M2M)
            accessors = []
            try:
                accessors.append(field.get_accessor_name())
            except Exception:
                pass
            accessors.append(field.name)

            for acc in accessors:
                if not acc:
                    continue
                related_attr = getattr(memory, acc, None)
                if related_attr is None:
                    continue
                # Si es un manager/queryset
                if hasattr(related_attr, "all"):
                    try:
                        qs = related_attr.all()
                        details_list = []
                        for obj in qs:
                            try:
                                details_list.append(model_to_dict(obj))
                            except Exception:
                                details_list.append({"id": getattr(obj, "pk", None)})
                        if details_list:
                            details[acc] = details_list
                    except Exception:
                        continue

        return Response({"memory": memory_data, "details": details}, status=status.HTTP_200_OK)


class FilterMemoriesView(APIView):
    """
    Endpoint para filtrar memorias por cualquier campo con validación de datos.
    
    Las configuraciones (campos válidos y choices) se obtienen dinámicamente del modelo,
    por lo que cualquier cambio en el modelo se reflejará automáticamente.
    
    Soporta filtros por:
    - id_memo: entero
    - titulo: texto (búsqueda parcial)
    - profesor: texto (búsqueda parcial)
    - descripcion: texto (búsqueda parcial, contains)
    - carrera: valor exacto de CareerChoices (obtenido del modelo)
    - entidad_involucrada: texto (búsqueda parcial)
    - tipo_entidad: texto (búsqueda parcial)
    - tipo_memoria: texto (búsqueda parcial)
    - fecha_inicio: fecha (YYYY-MM-DD) o año (YYYY)
    - fecha_termino: fecha (YYYY-MM-DD) o año (YYYY)
    - fecha_subida: fecha (YYYY-MM-DD) o año (YYYY)
    
    Ejemplo de uso:
    POST /api/memos/filter/
    {
        "filters": {
            "carrera": "INGINFO",
            "profesor": "Juan",
            "descripcion": "proyecto",
            "fecha_inicio": "2023"
        }
    }
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa el endpoint obteniendo las configuraciones del modelo."""
        super().__init__(*args, **kwargs)
        self.valid_fields = get_valid_fields()
        self.career_choices = get_career_choices()
        self.escuela_choices = get_escuela_choices()
        self.detalle_fields = get_detalle_valid_fields()
    
    def validate_field_value(self, field_name, value, is_detalle=False):
        """
        Valida que el valor sea apropiado para el campo.
        Retorna (es_válido, mensaje_error, valor_procesado)
        """
        # Determinar el tipo según si el campo es de detalle o del modelo principal
        field_type = None
        if is_detalle:
            field_type = self.detalle_fields.get(field_name)
        else:
            field_type = self.valid_fields.get(field_name)

        if not field_type:
            return False, f"Campo '{field_name}' no es válido para filtro.", None
        
        try:
            if field_type == 'integer':
                if not isinstance(value, int):
                    return False, f"El campo '{field_name}' debe ser un entero.", None
                return True, None, value
            
            elif field_type == 'string' or field_type == 'string_contains':
                if not isinstance(value, str):
                    return False, f"El campo '{field_name}' debe ser una cadena de texto.", None
                if len(value) == 0:
                    return False, f"El campo '{field_name}' no puede estar vacío.", None
                return True, None, value
            elif field_type == 'rut':
                # Validar formato de RUT utilizando el validador central
                try:
                    validar_rut(value)
                    return True, None, value
                except ValidationError:
                    return False, f"El RUT '{value}' no tiene un formato válido.", None
            
            elif field_type == 'choice':
                # choice puede corresponder a 'carrera' o 'escuela'
                if value not in self.career_choices and value not in self.escuela_choices:
                    valid_choices = ', '.join(list(self.career_choices.keys()) + list(self.escuela_choices.keys()))
                    return False, f"El valor '{value}' no es válido para el campo. Opciones válidas: {valid_choices}", None
                return True, None, value
            
            elif field_type == 'date':
                if not isinstance(value, str):
                    return False, f"El campo '{field_name}' debe ser una cadena de fecha.", None
                
                # Intentar parsear como fecha completa (YYYY-MM-DD)
                try:
                    datetime.strptime(value, '%Y-%m-%d')
                    return True, None, ('date', value)
                except ValueError:
                    pass
                
                # Intentar parsear como año (YYYY)
                try:
                    int(value)
                    if len(value) == 4 and value.isdigit():
                        return True, None, ('year', value)
                except ValueError:
                    pass
                
                return False, f"El campo '{field_name}' debe ser una fecha (YYYY-MM-DD) o año (YYYY).", None
        
        except Exception as e:
            return False, f"Error al validar campo '{field_name}': {str(e)}", None
    
    
    
    def build_query(self, filters):
        """
        Construye dos consultas Q separadas: una para `Memoria` y otra para `MemoriaDetalle`.

        Retorna: (memoria_query, detalle_query, errors)
        - `memoria_query` es un Q aplicable sobre `Memoria` (sin filtrar por detalles).
        - `detalle_query` es un Q aplicable sobre `MemoriaDetalle`.
        """
        memoria_q = None
        detalle_q = None
        errors = []

        for field_name, value in filters.items():
            base_field = field_name.replace('_year', '')
            is_detalle = base_field in self.detalle_fields

            # Validar el campo
            is_valid, error_msg, processed_value = self.validate_field_value(base_field, value, is_detalle=is_detalle)
            if not is_valid:
                errors.append(error_msg)
                continue

            try:
                if is_detalle:
                    # Construir consulta para MemoriaDetalle (sin prefijo)
                    field_type = self.detalle_fields.get(base_field)
                    q_part = Q(**({f"{base_field}__exact": processed_value} if field_type == 'rut' else {f"{base_field}__icontains": processed_value}))
                    if detalle_q is None:
                        detalle_q = q_part
                    else:
                        detalle_q &= q_part
                else:
                    # Consulta sobre Memoria
                    field_type = self.valid_fields.get(base_field)
                    if field_type == 'integer':
                        q_part = Q(**{f"{base_field}__exact": processed_value})
                    elif field_type == 'string' or field_type == 'string_contains':
                        q_part = Q(**{f"{base_field}__icontains": processed_value})
                    elif field_type == 'choice':
                        q_part = Q(**{f"{base_field}__exact": processed_value})
                    elif field_type == 'date':
                        if '_year' in field_name:
                            q_part = Q(**{f"{base_field}__year": int(processed_value[1])})
                        else:
                            q_part = Q(**{f"{base_field}__exact": processed_value[1]})
                    else:
                        q_part = Q()

                    if memoria_q is None:
                        memoria_q = q_part
                    else:
                        memoria_q &= q_part
            except Exception as e:
                errors.append(f"Error al procesar filtro '{field_name}': {str(e)}")

        return memoria_q, detalle_q, errors

    def post(self, request):
        """
        Recibe los filtros en el body y retorna las memorias filtradas.

        Lógica:
        1. Construir queries separadas para `MemoriaDetalle` y `Memoria`.
        2. Si hay filtros de detalle, consultar `MemoriaDetalle` y obtener ids de memorias.
        3. Si no hay ids que coincidan, retornar 0 resultados.
        4. Aplicar los filtros de Memoria y restringir por los ids obtenidos (si existen).
        5. Devolver solo los datos de Memoria.
        """
        try:
            filters = request.data.get('filters', {})

            if not isinstance(filters, dict):
                return Response({"error": "El campo 'filters' debe ser un objeto JSON."}, status=status.HTTP_400_BAD_REQUEST)

            if not filters:
                return Response({"error": "Debe proporcionar al menos un filtro."}, status=status.HTTP_400_BAD_REQUEST)

            memoria_q, detalle_q, errors = self.build_query(filters)
            if errors:
                return Response({"error": "Errores de validación en los filtros.", "details": errors}, status=status.HTTP_400_BAD_REQUEST)

            # Si hay filtros de detalle, buscar MemoriaDetalle primero
            ids = None
            if detalle_q is not None:
                detalle_qs = MemoriaDetalle.objects.filter(detalle_q)
                ids = list(detalle_qs.values_list('id_memo_id', flat=True).distinct())
                if not ids:
                    return Response({"count": 0, "results": []}, status=status.HTTP_200_OK)

            # Construir query final para Memoria
            if memoria_q is not None:
                final_q = memoria_q
            else:
                final_q = Q()

            if ids is not None:
                final_q &= Q(id_memo__in=ids)

            memories = Memoria.objects.filter(final_q).distinct()

            # Serializar resultados: solo datos de la Memoria (sin detalles)
            results = []
            for memory in memories:
                serializer = MemoriaSerializer(memory, context={'request': request})
                results.append(serializer.data)

            return Response({"count": len(results), "results": results}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Error interno del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
