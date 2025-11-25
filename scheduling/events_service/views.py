from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from core.models import Event, Workspace, EventSpace, StatusEvent
from core.serializers import EventSerializer, EventDetailSerializer, EventSpaceSerializer
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .services.google_forms import create_event_form


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by('-start_datetime')
    serializer_class = EventSerializer

    def create(self, request, *args, **kwargs):
        # Validar evento principal
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        create_invitation = serializer.validated_data.pop('create_invitation', False)

        # Validar detalle y espacios sin guardar aún
        detail_data = request.data.get("detail", None)
        spaces = request.data.get("spaces", None)

        if not detail_data:
            return Response({"error": "El detalle del evento es obligatorio."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not spaces or not isinstance(spaces, (list, tuple)):
            return Response({"error": "Los espacios del evento son obligatorios."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validar campos del detalle (sin el campo 'event' aún)
        detail_serializer = EventDetailSerializer(data=detail_data, partial=True)
        detail_serializer.is_valid(raise_exception=True)

        # Validar que todos los workspaces existan
        requested_space_ids = [int(s) for s in spaces]
        existing_space_ids = list(Workspace.objects.filter(id_workspace__in=requested_space_ids).values_list('id_workspace', flat=True))
        missing = set(requested_space_ids) - set(existing_space_ids)
        if missing:
            return Response({"error": "Algunos espacios no existen.", "missing_space_ids": list(missing)},
                            status=status.HTTP_400_BAD_REQUEST)

        #* Todo validado: crear registros dentro de una transacción atómica
        try:
            with transaction.atomic():
                event = serializer.save()

                # Guardar detalle asociándolo al evento creado
                detail_data_for_save = dict(detail_serializer.validated_data)
                detail_data_for_save['event'] = event.id_event
                detail_for_save = EventDetailSerializer(data=detail_data_for_save)
                detail_for_save.is_valid(raise_exception=True)
                event_detail = detail_for_save.save()

                # Crear EventSpace en bloque
                event_space_objs = [EventSpace(event=event, workspace_id=wid) for wid in existing_space_ids]
                EventSpace.objects.bulk_create(event_space_objs)

                # Si se solicita crear invitación externa
                if create_invitation:
                    result = create_event_form(event.title)
                    if result:
                        event.form_edit_link = result.get("edit_link")
                        event.form_public_link = result.get("public_link")
                        event.save()

        except Exception as e:
            return Response({"error": "Error al crear el evento.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Preparar respuesta con datos del evento creado
        response_data = EventSerializer(event).data
        response_data.update({
            'detail': EventDetailSerializer(event_detail).data,
            'spaces': existing_space_ids,
        })
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['POST'])
    def generate_invitation(self, request, pk=None):
        event = self.get_object()
        if event.form_public_link:
            return Response({"message": "Invitación ya creada"},
                            status=status.HTTP_400_BAD_REQUEST)

        form_data = create_google_form(event.title)
        if form_data:
            event.form_public_link = form_data.get('form_public_link')
            event.form_edit_link = form_data.get('form_edit_link')
            event.save()
            return Response({
                "form_public_link": event.form_public_link,
                "form_edit_link": event.form_edit_link
            }, status=status.HTTP_200_OK)

        return Response({"message": "Error al generar invitación"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #! /user/{user_id}
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        User = get_user_model()
        user = get_object_or_404(User, id=user_id)
        schedules = Event.objects.filter(user=user).order_by('-start_time')

        if not schedules.exists():
            return Response({"message": "Este usuario no tiene solicitudes registradas."},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_future_activity(request):
    now = timezone.now()
    
    # Traer eventos futuros o activos
    events = Event.objects.filter(
        Q(start_datetime__gte=now) | Q(end_datetime__gte=now)
    )
    
    # Filtrar por espacios si se proporcionan (no si all=true)
    all_events = request.query_params.get('all', 'false').lower() == 'true'
    
    if not all_events:
        spaces_param = request.query_params.get('spaces', '')
        if spaces_param:
            try:
                space_ids = [int(space_id.strip()) for space_id in spaces_param.split(',') if space_id.strip()]
                if space_ids:
                    # Filtrar eventos que tengan al menos uno de los espacios solicitados
                    events = events.filter(eventspace__workspace_id__in=space_ids).distinct()
            except (ValueError, AttributeError):
                return Response(
                    {"error": "El parámetro 'spaces' debe ser una lista de IDs separados por comas."},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    events = events.order_by('start_datetime')

    return Response({
        'events': EventSerializer(events, many=True).data
    })


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_scheduled_events(request):
    """
    Obtiene eventos con status AGENDED, CONFIRMED e IN_COURSE.
    
    Parámetros:
    - today (bool): Si es true, obtiene solo eventos del día actual (que empiecen hoy, estén en curso o terminen hoy).
                    Si es false, obtiene todos los eventos futuros exceptuando IN_COURSE (a menos que estén activos).
    """
    now = timezone.now()
    today = request.query_params.get('today', 'false').lower() == 'true'
    
    # Definir los estados permitidos
    allowed_statuses = [
        StatusEvent.AGENDED,      # 1
        StatusEvent.CONFIRMED,    # 2
        StatusEvent.IN_COURSE     # 3
    ]
    
    if today:
        # Filtrar solo eventos del día actual
        # Incluye: eventos que empiezan hoy, están en curso, o terminan hoy
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        events = Event.objects.filter(
            Q(status__in=allowed_statuses) &
            (
                Q(start_datetime__date=today_start.date()) |  # Empieza hoy
                Q(end_datetime__date=today_start.date()) |    # Termina hoy
                (Q(start_datetime__lte=now) & Q(end_datetime__gte=now))  # En curso
            )
        )
    else:
        # Filtrar eventos futuros:
        # - AGENDED y CONFIRMED: cuya fecha de inicio sea mayor a hoy
        # - IN_COURSE: cuya fecha de término aún no haya pasado
        events = Event.objects.filter(
            Q(status__in=[StatusEvent.AGENDED, StatusEvent.CONFIRMED], start_datetime__gte=now) |
            Q(status=StatusEvent.IN_COURSE, end_datetime__gte=now)
        )
    
    events = events.order_by('start_datetime')

    return Response({
        'events': EventSerializer(events, many=True).data
    })

