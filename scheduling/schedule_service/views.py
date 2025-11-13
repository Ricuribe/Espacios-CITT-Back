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
    ViewSet para listar, obtener y detallar un workspace junto con sus recursos.
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
