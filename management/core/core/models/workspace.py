from django.db import models
from django.conf import settings
import os
from django.utils.deconstruct import deconstructible
from .__base__ import BaseModel

class Zona(models.TextChoices):
    NO = 'NO', 'Noroeste'
    NE = 'NE', 'Noreste'
    CO = 'CO', 'Centro Oeste'
    CE = 'CE', 'Centro Este'
    SE = 'SE', 'Sudeste'
    SO = 'SO', 'Sudoeste'

class Workspace(BaseModel, models.Model):
    id_workspace = models.AutoField(primary_key=True, db_column='id_espacio')
    name = models.CharField(max_length=100, db_column='nombre', verbose_name='Nombre')
    space_type = models.CharField(max_length=50, db_column='tipo_espacio', verbose_name='Tipo de espacio')
    description = models.TextField(db_column='descripcion', verbose_name='Descripción')
    max_occupancy = models.IntegerField(db_column='aforo_maximo', verbose_name='Aforo máximo')
    zone_space = models.CharField(max_length=2, choices=Zona.choices, unique=True, db_column='zona_espacio', verbose_name='Zona del espacio')
    enabled = models.BooleanField(default=True, db_column='habilitado', verbose_name='¿Habilitado?')
    
    class Meta:
        db_table = 'espacios'
        verbose_name = 'Espacio'
        verbose_name_plural = 'Espacios'

    def __str__(self):
        return f"{self.name} ({self.get_zone_space_display()})" 
    
    def save(self, *args, **kwargs):
        
        if Workspace.objects.filter(zone_space=self.zone_space):
            existing = Workspace.objects.get(zone_space=self.zone_space)
            if self.pk != existing.pk:
                raise ValueError(f"Ya existe un espacio en la zona {self.get_zone_space_display()}.")
        super().save(*args, **kwargs)


class WorkspaceResource(BaseModel, models.Model):
    id_resource = models.AutoField(primary_key=True, db_column='id_recurso')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, db_column='espacio')
    resource_name = models.CharField(max_length=100, db_column='nombre_recurso', verbose_name='Nombre del recurso')
    quantity = models.IntegerField(db_column='cantidad', verbose_name='Cantidad')

    class Meta:
        db_table = 'recursos_espacio'
        verbose_name = 'Recurso de espacio'
        verbose_name_plural = 'Recursos de espacios'

    def __str__(self):
        return f"{self.resource_name} in {self.workspace.name}"


@deconstructible
class TableImagePath:
    """
    Define la ruta de subida personalizada para imágenes de las mesas.
    """
    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        if getattr(instance, 'id_table', None):
            filename = f"table_{instance.id_table}.{ext}"
        else:
            filename = f"table_temp.{ext}"
        return os.path.join("table_images/", filename)

class Table(BaseModel, models.Model):
    id_table = models.AutoField(primary_key=True, db_column='id_mesa')
    table_name = models.CharField(max_length=100, db_column='nombre_mesa', verbose_name='Nombre de la mesa')
    table_type = models.CharField(max_length=50, db_column='tipo_mesa', verbose_name='Tipo de mesa')
    capacity = models.IntegerField(db_column='capacidad', verbose_name='Capacidad')
    movable = models.BooleanField(db_column='es_movil', verbose_name='¿Es móvil?')
    description = models.TextField(db_column='descripcion', verbose_name='Descripción')
    image = models.ImageField(upload_to=TableImagePath(), null=True, blank=True, db_column='imagen')
    
    class Meta:
        db_table = 'mesas'
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'
    
    def save(self, *args, **kwargs):
        try:
            old = Table.objects.get(pk=self.pk)
            if old.image and self.image != old.image:
                old.image.delete(save=False)
        except Table.DoesNotExist:
            pass

        super().save(*args, **kwargs)

        # Si el objeto se acaba de crear y tenía una imagen temporal,
        # renombramos el archivo con el ID real
        if self.image and "table_temp" in self.image.name:
            ext = self.image.name.split('.')[-1]
            new_name = f"table_{self.id_table}.{ext}"
            new_path = os.path.join("static/table_images", new_name)

            from django.core.files.storage import default_storage
            old_path = self.image.name

            file = default_storage.open(old_path)
            self.image.save(new_path, file, save=False)
            file.close()

            default_storage.delete(old_path)

            super().save(update_fields=["image"])

    def __str__(self):
        return self.name