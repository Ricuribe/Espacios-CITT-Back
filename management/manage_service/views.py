from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from core.models import Workspace, WorkspaceResource
from core.serializers import (
    WorkspaceSerializer,
    WorkspaceResourceSerializer
)


class WorkspaceViewSet(viewsets.ViewSet):
    """
    ViewSet para:
    - Listar, obtener y detallar un workspace junto con sus recursos.
    - Permitir la gestión de workspaces y sus recursos asociados.
    - Proporcionar endpoints para interactuar con los workspaces.
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
    
