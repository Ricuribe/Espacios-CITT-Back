import os
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Memoria
from django.forms.models import model_to_dict
from .serializers import MemoriaSerializer


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
