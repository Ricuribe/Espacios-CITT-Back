from django.db import models
from django.core.exceptions import ValidationError
import os
from django.utils.deconstruct import deconstructible
from django.core.files.storage import default_storage

# --- validador personalizado ---
def validar_pdf(value):
    """
    Valida si el archivo es un PDF.
    """
    if not value.name.lower().endswith('.pdf'):
        raise ValidationError('Solo se permiten archivos en formato PDF.')

def validar_rut(value):
    """
    Validador simple para RUT.
    
    """
    import re
    pattern = r'^\d{1,2}\.\d{3}\.\d{3}-[0-9kK]$|^\d{7,8}-[0-9kK]$'
    if not re.match(pattern, value):
        raise ValidationError('El RUT no tiene un formato válido.')
    
@deconstructible
class RenamePDFPath:
    """
    Clase para definir la ruta de subida personalizada para archivos PDF de Memoria.
    Si el objeto aún no tiene ID (aún no se ha guardado), se asigna un nombre temporal.
    """
    def __call__(self, instance, filename):
        
        ext = filename.split('.')[-1] 
        if instance.id_memo:
            filename = f"memoria_{instance.id_memo}.{ext}"
        else:
            filename = f"memoria_temp.{ext}"
        return os.path.join("memorias/", filename)

@deconstructible
class RenameImagePath:
    """
    Clase para definir la ruta de subida personalizada para imágenes de Memoria.
    Si el objeto aún no tiene ID (aún no se ha guardado), se asigna un nombre temporal.
    """

    def __call__(self, instance, filename):
        
        ext = filename.split('.')[-1] 
        if instance.id_memo:
            filename = f"memoimg_{instance.id_memo}.{ext}"
        else:
            filename = f"memoimg_temp.{ext}"
        return os.path.join("memo_images/", filename)
    
class CareerChoices(models.TextChoices):
    INGENIERIA_EN_INFORMATICA = 'INGINFO', 'Ingeniería en Informática'
    TECNICO_ANALISTA_PROGRAMADOR = 'TAP', 'Técnico Analista Programador'
    TECNICO_REDES_Y_TELECOMUNICACIONES = 'TRT', 'Técnico en Redes y Telecomunicaciones'
    INGENIERIA_EN_TELECOMUNICACIONES = 'INGTEL', 'Ingeniería en Redes y Telecomunicaciones'


# --- modelo principal ---
class Memoria(models.Model):
    id_memo = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    profesor = models.CharField(max_length=100)
    descripcion = models.TextField()
    carrera = models.CharField(
        max_length=50,
        choices=CareerChoices.choices
    )
    loc_disco = models.FileField(
        upload_to=RenamePDFPath(),
        validators=[validar_pdf]
    )
    imagen_display = models.ImageField(
        upload_to=RenameImagePath(),
        blank=True,
        null=True
    )
    fecha_inicio = models.DateField()
    fecha_termino = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'memorias'
        verbose_name = 'Memoria'
        verbose_name_plural = 'Memorias'

    def save(self, *args, **kwargs):
        """
        Al guardar, si el objeto ya existía y la imagen/archivo cambió, eliminar el anterior.
        Después del primer guardado renombrar los archivos temporales generados por
        `RenameImagePath` y `RenamePDFPath` para usar el id real (`id_memo`).
        """
        try:
            old = Memoria.objects.get(pk=self.pk)
            if old.imagen_display and self.imagen_display != old.imagen_display:
                old.imagen_display.delete(save=False)
            if old.loc_disco and self.loc_disco != old.loc_disco:
                old.loc_disco.delete(save=False)
        except Memoria.DoesNotExist:
            # objeto nuevo
            pass

        super().save(*args, **kwargs)

        # Renombrar imagen temporal si existe
        if self.imagen_display and "memoimg_temp" in os.path.basename(self.imagen_display.name):
            ext = self.imagen_display.name.split('.')[-1]
            new_name = f"memoimg_{self.id_memo}.{ext}"
            new_path = os.path.join("memo_images", new_name)

            old_path = self.imagen_display.name
            file = default_storage.open(old_path)
            # guardar con nuevo nombre en storage
            self.imagen_display.save(new_path, file, save=False)
            file.close()
            # borrar antiguo
            default_storage.delete(old_path)

            super().save(update_fields=["imagen_display"])

        # Renombrar PDF temporal si existe
        if self.loc_disco and "memoria_temp" in os.path.basename(self.loc_disco.name):
            ext = self.loc_disco.name.split('.')[-1]
            new_name = f"memoria_{self.id_memo}.{ext}"
            new_path = os.path.join("memorias", new_name)

            old_path = self.loc_disco.name
            file = default_storage.open(old_path)
            self.loc_disco.save(new_path, file, save=False)
            file.close()
            default_storage.delete(old_path)

            super().save(update_fields=["loc_disco"])

    def __str__(self):
        return self.titulo


class MemoriaDetalle(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_memo = models.ForeignKey(
        Memoria,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    rut_estudiante = models.CharField(max_length=12 , validators=[validar_rut])
    nombre_estudiante = models.CharField(max_length=30)
    apellido_estudiante = models.CharField(max_length=30)
    segundo_nombre_estudiante = models.CharField(max_length=30, blank=True, null=True)
    segundo_apellido_estudiante = models.CharField(max_length=30, blank=True, null=True)
    linkedin = models.URLField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'memorias_detalles'
        verbose_name = 'Detalle de Memoria'
        verbose_name_plural = 'Detalles de Memorias'

    def __str__(self):
        return f"{self.rut_estudiante} {self.nombre_estudiante} {self.apellido_estudiante}".strip()
