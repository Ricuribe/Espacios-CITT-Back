from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import Memoria, MemoriaDetalle
from .serializers import MemoriaSerializer, MemoriaDetalleSerializer
import json


class MemoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar memorias con operaciones CRUD completas.
    
    Soporta:
    - GET /memories/ : Listar todas las memorias
    - POST /memories/ : Crear una nueva memoria
    - GET /memories/{id}/ : Obtener detalles de una memoria
    - PUT /memories/{id}/ : Actualizar una memoria completa
    - PATCH /memories/{id}/ : Actualizar parcialmente una memoria
    - DELETE /memories/{id}/ : Eliminar una memoria y sus detalles
    - POST /memories/{id}/add_detalle/ : Agregar un detalle a una memoria
    - PUT /memories/{id}/update_detalle/{detalle_id}/ : Actualizar un detalle
    - DELETE /memories/{id}/delete_detalle/{detalle_id}/ : Eliminar un detalle
    - GET /memories/{id}/detalles/ : Obtener todos los detalles de una memoria
    """
    queryset = Memoria.objects.all()
    serializer_class = MemoriaSerializer

    def create(self, request, *args, **kwargs):
        """
        Crea una nueva memoria con opción de incluir detalles en la misma solicitud.
        
        Payload esperado (SIN detalles):
        {
            "titulo": "string",
            "profesor": "string",
            "descripcion": "string",
            "carrera": "string (choice)",
            "escuela": "string (choice)",
            "loc_disco": "file (PDF)",
            "imagen_display": "file (image, opcional)",
            "entidad_involucrada": "string",
            "tipo_entidad": "string",
            "tipo_memoria": "string",
            "fecha_inicio": "YYYY-MM-DD",
            "fecha_termino": "YYYY-MM-DD",
            "fecha_subida": "YYYY-MM-DD"
        }
        
        Payload esperado (CON detalles):
        {
            "titulo": "string",
            "profesor": "string",
            "descripcion": "string",
            "carrera": "string (choice)",
            "escuela": "string (choice)",
            "loc_disco": "file (PDF)",
            "imagen_display": "file (image, opcional)",
            "entidad_involucrada": "string",
            "tipo_entidad": "string",
            "tipo_memoria": "string",
            "fecha_inicio": "YYYY-MM-DD",
            "fecha_termino": "YYYY-MM-DD",
            "fecha_subida": "YYYY-MM-DD"
            "detalles": [
                {
                    "rut_estudiante": "XX.XXX.XXX-X",
                    "nombre_estudiante": "string",
                    "apellido_estudiante": "string",
                    "segundo_nombre_estudiante": "string (opcional)",
                    "segundo_apellido_estudiante": "string (opcional)",
                    "linkedin": "URL (opcional)"
                },
                ...
            ]
        }
        """
        # Extraer y normalizar detalles del payload
        detalles_data = self._extract_and_parse_detalles(request.data.pop('detalles', []))
        if isinstance(detalles_data, Response):
            return detalles_data
        
        # Crear la memoria
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        memoria = serializer.save()
        
        # Crear los detalles si se proporcionaron
        detalles_creados = []
        detalles_errores = []
        
        for idx, detalle_data in enumerate(detalles_data):
            # Hacer una copia para no modificar el original
            if isinstance(detalle_data, dict):
                detalle_data = detalle_data.copy()
            else:
                detalles_errores.append({
                    "index": idx,
                    "errores": {"detalle": "El detalle debe ser un objeto JSON."}
                })
                continue
            
            detalle_data['id_memo'] = memoria.id_memo
            detalle_serializer = MemoriaDetalleSerializer(data=detalle_data)
            
            if detalle_serializer.is_valid():
                detalle_serializer.save()
                detalles_creados.append(detalle_serializer.data)
            else:
                detalles_errores.append({
                    "index": idx,
                    "errores": detalle_serializer.errors
                })
        
        # Preparar respuesta
        response_data = serializer.data
        response_data['detalles_creados'] = detalles_creados
        
        if detalles_errores:
            response_data['detalles_con_errores'] = detalles_errores
            response_data['advertencia'] = "La memoria fue creada exitosamente, pero hubo errores al crear algunos detalles."
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
    
    def _extract_and_parse_detalles(self, detalles_raw):
        """
        Extrae y parsea el campo 'detalles' que puede venir en múltiples formatos:
        - Como lista de dicts (JSON puro)
        - Como string JSON (multipart form-data)
        - Como lista con un string adentro (QueryDict.pop() behavior)
        
        Retorna:
        - Lista de dicts si es válido
        - Response con error si hay problemas
        """
        if not detalles_raw:
            return []
        
        # Caso 1: Si es una lista con un string adentro (QueryDict behavior)
        if isinstance(detalles_raw, list) and len(detalles_raw) > 0:
            detalles_raw = detalles_raw[0]
        
        # Caso 2: Si es un string, parsearlo como JSON
        if isinstance(detalles_raw, str):
            try:
                detalles_data = json.loads(detalles_raw.strip())
            except (json.JSONDecodeError, ValueError) as e:
                return Response(
                    {"error": f"El campo 'detalles' debe ser un JSON válido. Error: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            detalles_data = detalles_raw
        
        # Caso 3: Validar que sea una lista
        if not isinstance(detalles_data, list):
            return Response(
                {"error": "El campo 'detalles' debe ser un array de objetos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return detalles_data

    def update(self, request, *args, **kwargs):
        """
        Actualiza una memoria existente (reemplaza todos los campos).
        Opcionalmente, puede actualizar solo algunos campos usando PATCH.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Elimina una memoria y todos sus detalles asociados.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": f"Memoria {instance.id_memo} y todos sus detalles han sido eliminados."},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['get'], url_path='detalles')
    def get_detalles(self, request, pk=None):
        """
        Obtiene todos los detalles asociados a una memoria.
        
        GET /memories/{id}/detalles/
        """
        memoria = self.get_object()
        detalles = memoria.detalles.all()
        serializer = MemoriaDetalleSerializer(detalles, many=True)
        return Response({
            "memoria_id": memoria.id_memo,
            "titulo": memoria.titulo,
            "total_detalles": detalles.count(),
            "detalles": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='add_detalle')
    def add_detalle(self, request, pk=None):
        """
        Agrega un nuevo detalle a una memoria existente.
        
        POST /memories/{id}/add_detalle/
        
        Payload esperado:
        {
            "rut_estudiante": "XX.XXX.XXX-X",
            "nombre_estudiante": "string",
            "apellido_estudiante": "string",
            "segundo_nombre_estudiante": "string (opcional)",
            "segundo_apellido_estudiante": "string (opcional)",
            "linkedin": "URL (opcional)"
        }
        """
        memoria = self.get_object()
        # Convertir request.data a diccionario mutable
        data = dict(request.data)
        data['id_memo'] = memoria.id_memo

        serializer = MemoriaDetalleSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Detalle agregado exitosamente.",
                    "detalle": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put', 'patch'], url_path=r'update_detalle/(?P<detalle_id>\d+)')
    def update_detalle(self, request, pk=None, detalle_id=None):
        """
        Actualiza un detalle específico de una memoria.
        
        PUT /memories/{id}/update_detalle/{detalle_id}/
        PATCH /memories/{id}/update_detalle/{detalle_id}/
        
        Payload esperado (PUT requiere todos los campos, PATCH solo los que desea actualizar):
        {
            "rut_estudiante": "XX.XXX.XXX-X (opcional en PATCH)",
            "nombre_estudiante": "string (opcional en PATCH)",
            "apellido_estudiante": "string (opcional en PATCH)",
            "segundo_nombre_estudiante": "string (opcional)",
            "segundo_apellido_estudiante": "string (opcional)",
            "linkedin": "URL (opcional)"
        }
        """
        memoria = self.get_object()
        detalle = get_object_or_404(MemoriaDetalle, id_detalle=detalle_id, id_memo=memoria)
        
        # Convertir request.data a diccionario mutable
        data = dict(request.data)
        partial = request.method == 'PATCH'
        serializer = MemoriaDetalleSerializer(detalle, data=data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Detalle actualizado exitosamente.",
                    "detalle": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path=r'delete_detalle/(?P<detalle_id>\d+)')
    def delete_detalle(self, request, pk=None, detalle_id=None):
        """
        Elimina un detalle específico de una memoria.
        
        DELETE /memories/{id}/delete_detalle/{detalle_id}/
        """
        memoria = self.get_object()
        detalle = get_object_or_404(MemoriaDetalle, id_detalle=detalle_id, id_memo=memoria)
        detalle_info = f"{detalle.rut_estudiante} - {detalle.nombre_estudiante} {detalle.apellido_estudiante}"
        detalle.delete()
        
        return Response(
            {
                "message": f"Detalle '{detalle_info}' eliminado exitosamente.",
                "detalle_id": detalle_id
            },
            status=status.HTTP_204_NO_CONTENT
        )
    
