from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from core.models import Workspace, WorkspaceResource, Event, EventDetail, RejectReason, EventSpace
from core.models.event import StatusEvent
from core.serializers import (
    WorkspaceSerializer,
    WorkspaceResourceSerializer,
    EventSerializer,
    EventDetailSerializer,
    EventSpaceSerializer
)


class WorkspaceViewSet(viewsets.ViewSet):
    """
    ViewSet que proporciona endpoints para interactuar con los workspaces:
    - Listar, obtener y detallar un workspace junto con sus recursos.
    - Permitir la gestión de workspaces y sus recursos asociados.
    - Editar o eliminar individualmente recursos de un Espacio.
    """

    def list(self, request):
        workspaces = Workspace.objects.all()
        serializer = WorkspaceSerializer(workspaces, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            workspace = Workspace.objects.get(pk=pk)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        workspace_serializer = WorkspaceSerializer(workspace, context={'request': request})
        resources = WorkspaceResource.objects.filter(workspace=workspace)
        resources_serializer = WorkspaceResourceSerializer(resources, many=True)

        data = workspace_serializer.data

        data["resources"] = resources_serializer.data

        return Response(data)

    #crea workspace y luego los recursos asociados
    def create(self, request):
        workspace_serializer = WorkspaceSerializer(data=request.data)
        if workspace_serializer.is_valid():
            workspace = workspace_serializer.save()

            resources_data = request.data.get("resources", [])
            for resource_data in resources_data:
                resource_data["workspace"] = workspace.id
                resource_serializer = WorkspaceResourceSerializer(data=resource_data)
                if resource_serializer.is_valid():
                    resource_serializer.save()
                else:
                    workspace.delete()
                    return Response(resource_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(workspace_serializer.data, status=status.HTTP_201_CREATED)
        return Response(workspace_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Actualiza workspace y/o sus recursos asociados
    def update(self, request, pk=None):
        workspace = get_object_or_404(Workspace, pk=pk)
        workspace_serializer = WorkspaceSerializer(workspace, data=request.data, partial=True)
        if workspace_serializer.is_valid():
            workspace_serializer.save()

            resources_data = request.data.get("resources", [])
            for resource_data in resources_data:
                resource_id = resource_data.get("id", None)
                if resource_id:
                    resource = get_object_or_404(WorkspaceResource, pk=resource_id, workspace=workspace)
                    resource_serializer = WorkspaceResourceSerializer(resource, data=resource_data, partial=True)
                else:
                    resource_data["workspace"] = workspace.id
                    resource_serializer = WorkspaceResourceSerializer(data=resource_data)

                if resource_serializer.is_valid():
                    resource_serializer.save()
                else:
                    return Response(resource_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(workspace_serializer.data)
        return Response(workspace_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class WorkspaceResourceViewSet(viewsets.ViewSet):
    """
    ViewSet para gestionar recursos individuales de un workspace.
    """

    def retrieve(self, request, pk=None):
        resource = get_object_or_404(WorkspaceResource, pk=pk)
        serializer = WorkspaceResourceSerializer(resource)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        resource = get_object_or_404(WorkspaceResource, pk=pk)
        resource.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def update(self, request, pk=None):
        resource = get_object_or_404(WorkspaceResource, pk=pk)
        serializer = WorkspaceResourceSerializer(resource, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request):
        serializer = WorkspaceResourceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class EventsManagementViewSet(viewsets.ViewSet):
    """
    ViewSet para gestionar y moderar eventos dentro del sistema.
    """
    
    def list(self, request):
        events = Event.objects.all()
        serializer = EventSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)
    
    # Obtener eventos por estado
    @action(detail=False, methods=['get'], url_path='by-status/(?P<status>[^/.]+)')
    def by_status(self, request, status=None):
        if status is not None and int(status) in dict(StatusEvent.choices).keys():
            events = Event.objects.filter(status=int(status))
            serializer = EventSerializer(events, many=True, context={'request': request})
            return Response(serializer.data)
        return Response({"error": "Estado inválido."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Filtrar eventos por: creador, rango de fechas, estado, titulo, tipo de evento y espacios
    @action(detail=False, methods=['get'], url_path='filter')
    def filter_events(self, request):
        events = Event.objects.all()
        
        creator_id = request.query_params.get('creator_id', None)
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        status_param = request.query_params.get('status', None)
        title = request.query_params.get('title', None)
        event_type = request.query_params.get('event_type', None)
        workspace_id = request.query_params.get('workspace_id', None)

        if creator_id:
            events = events.filter(created_by__id=creator_id)
        if start_date and end_date:
            events = events.filter(start_datetime__gte=start_date, end_datetime__lte=end_date)
        if status_param and int(status_param) in dict(StatusEvent.choices).keys():
            events = events.filter(status=int(status_param))
        if title:
            events = events.filter(title__icontains=title)
        if event_type:
            events = events.filter(eventdetail__event_type__icontains=event_type)
        if workspace_id:
            events = events.filter(eventspace__workspace__id=workspace_id[0])
        if workspace_id.length > 1:
            events = events.filter(eventspace__workspace__id__in=workspace_id).distinct()

        serializer = EventSerializer(events, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    # Obtener detalle de un evento
    def retrieve(self, request, pk=None):
        event = get_object_or_404(Event, pk=pk)
        event_creator = get_user_model().objects.get(pk=event.created_by.id)
        event_detail = get_object_or_404(EventDetail, event=event)
        event_spaces = EventSpace.objects.filter(event=event)
        event_spaces_serializer = EventSpaceSerializer(event_spaces, many=True, context={'request': request})
        event_serializer = EventSerializer(event, context={'request': request})
        event_detail_serializer = EventDetailSerializer(event_detail, context={'request': request})
        data = event_serializer.data
        data["creator"] = {"username": event_creator.username, "email": event_creator.email}
        data["detail"] = event_detail_serializer.data
        data["spaces"] = event_spaces_serializer.data
        return Response(data, status=status.HTTP_200_OK)
        
    # Actualizar estado del evento
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        event = get_object_or_404(Event, pk=pk)
        new_status = request.data.get("status", None)
        if new_status is not None and new_status in dict(StatusEvent.choices).keys():
            event.status = new_status
            event.save()
            
            if new_status == StatusEvent.REJECT:
                reason_text = request.data.get("reason", "")
                RejectReason.objects.update_or_create(event=event, defaults={"reason": reason_text})
                return Response({"message": "Evento rechazado con motivo registrado."})
            
            return Response({"message": "Estado del evento actualizado correctamente."})
        return Response({"error": "Estado inválido."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Editar duracion de un evento
    @action(detail=True, methods=['post'])
    def edit_duration(self, request, pk=None):
        event = get_object_or_404(Event, pk=pk)
        new_start = request.data.get("start_datetime", None)
        new_end = request.data.get("end_datetime", None)
        
        if new_start:
            event.start_datetime = new_start
        if new_end:
            event.end_datetime = new_end
        
        event.save()
        return Response({"message": "Duración del evento actualizada correctamente."})
    
    