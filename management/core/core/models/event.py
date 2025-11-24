from django.db import models
from django.conf import settings
from .__base__ import BaseModel
from .workspace import Workspace

class StatusEvent(models.IntegerChoices):
    CANCELL = 0, 'Cancelado'
    AGENDED = 1, 'Agendado'
    CONFIRMED = 2, 'Confirmado'
    IN_COURSE = 3, 'En curso'
    COMPLETED = 4, 'Realizado'
    REJECT = 5, 'Rechazado'

class Event(BaseModel, models.Model):
    id_event = models.AutoField(primary_key=True, db_column='id_evento')
    title = models.CharField(max_length=200, db_column='titulo', verbose_name='Título')
    start_datetime = models.DateTimeField(db_column='inicio')
    end_datetime = models.DateTimeField(db_column='termino')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events', db_column='creado_por')
    form_public_link = models.URLField(blank=True, null=True, db_column='enlace_form_publico')
    form_edit_link = models.URLField(blank=True, null=True, db_column='enlace_form_edicion')
    status = models.IntegerField(choices=StatusEvent.choices, default=StatusEvent.AGENDED, db_column='estado', verbose_name='Estado del evento')

    class Meta:
        db_table = 'eventos'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return f"{self.title} ({self.start_datetime} - {self.end_datetime})"

class EventDetail(BaseModel, models.Model):
    id_detail = models.AutoField(primary_key=True, db_column='id_detalle')
    event_type = models.CharField(max_length=100, default='Evento Académico', db_column='tipo_evento', verbose_name='Tipo de evento')
    event = models.OneToOneField(Event, on_delete=models.CASCADE, db_column='agenda')
    attendees = models.IntegerField(db_column='asistentes', verbose_name='Total de asistentes' , db_comment='Número máximo de asistentes')
    description = models.TextField(blank=True, db_column='descripcion', verbose_name='Descripción')
    
    class Meta:
        db_table = 'detalle_evento'
        verbose_name = 'Detalle de evento'
        verbose_name_plural = 'Detalles de evento'

    def __str__(self):
        return f"Detail for {self.event.id_event} - {self.event.title}"
    
class EventSpace(BaseModel, models.Model):
    id_detail_space = models.AutoField(primary_key=True, db_column='id_espacio')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, db_column='evento')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, db_column='espacio_trabajo')
    
    class Meta:
        db_table = 'espacios_evento'
        verbose_name = 'Espacio de evento'
        verbose_name_plural = 'Espacios de eventos'

    def __str__(self):
        return f"Event {self.event.id_event} in Workspace {self.workspace.id_workspace}"
    
class RejectReason(BaseModel, models.Model):
    id_reason = models.AutoField(primary_key=True, db_column='id_motivo')
    event = models.OneToOneField(Event, on_delete=models.CASCADE, db_column='agenda')
    reason = models.TextField(db_column='motivo')

    class Meta:
        db_table = 'motivos_rechazo'
        verbose_name = 'Motivo de rechazo'
        verbose_name_plural = 'Motivos de rechazo'

    def __str__(self):
        return f"Rejection for {self.event.title}: {self.reason}"