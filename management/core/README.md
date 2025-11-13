management.core
=================

Esta app centraliza modelos y serializadores reutilizables para el proyecto.

Tablas (nombres en español en la base de datos):

- Espacio: `espacios` (modelo `Workspace`)
  - Columnas principales: `id_espacio`, `nombre`, `tipo_espacio`, `descripcion`, `aforo_maximo`, `imagen`

- Recursos de espacio: `recursos_espacio` (modelo `WorkspaceResource`)
  - Columnas principales: `id_recurso`, `espacio`, `nombre_recurso`, `cantidad`

- Agendas: `agendas` (modelo `Schedule`)
  - Columnas principales: `id_agenda`, `usuario`, `inicio`, `fin`, `espacio`, `estado`, `fecha_agendada`

- Detalle de agenda: `detalle_agenda` (modelo `ScheduleDetail`)
  - Columnas principales: `id_detalle`, `agenda`, `equipo`, `asistentes`, `proyecto`, `descripcion`

- Motivos de rechazo: `motivos_rechazo` (modelo `RejectionReason`)
  - Columnas principales: `id_motivo`, `agenda`, `motivo`

- Eventos: `eventos` (modelo `Event`)
  - Columnas principales: `id_evento`, `titulo`, `tipo_evento`, `descripcion`, `inicio`, `termino`, `creado_por`, `enlace_form_publico`, `enlace_form_edicion`

Cómo importar
--------------
Usar directamente las importaciones desde la app `core`:

```python
from core.models import Workspace, Schedule, Event
from core.serializers import WorkspaceSerializer, ScheduleSerializer
```

Compatibilidad con código antiguo
---------------------------------
- Para evitar romper migraciones históricas, los módulos antiguos en `scheduling` contienen proxies y helpers (p. ej. `WorkspaceImagePath`) que reexportan símbolos desde `management.core`.
- Estos proxies están marcados como obsoletos y deben ser eliminados en una etapa futura cuando el código consumidor se actualice.

Proxies existentes (deprecación)
--------------------------------
Actualmente existen los siguientes proxies que mantienen compatibilidad con imports antiguos:

- `scheduling/schedule_service/models.py` — reexporta `Workspace`, `Schedule`, `ScheduleDetail`, `WorkspaceImagePath`, `RejectionReason` y emite una advertencia deprecatoria.
- `scheduling/events_service/models.py` — reexporta `Event` y emite una advertencia deprecatoria.

Plan de eliminación segura de proxies
------------------------------------
1. Actualizar todo el código consumidor para importar desde `management.core.models` y `management.core.serializers`.
2. Ejecutar la suite de tests y aplicar migraciones en un entorno de staging.
3. Eliminar los archivos proxy y cualquier referencia residual.
4. Bump de versión si `management.core` se publica como paquete.

Si quieres, puedo automatizar el paso 1 (buscar y reemplazar imports) y generar un PR con los cambios; también puedo listar todos los archivos que aún usan los proxies.

Flujo recomendado al cambiar `management.core`
---------------------------------------------
1. Si cambias solo lógica interna (no renombrar campos ni tablas):
   - Ejecuta tests.
   - Reinicia el servidor (runserver / gunicorn) para cargar los cambios.

2. Si cambias modelos (añadir/quitar/cambiar campos o db_table/db_column):
   - Crear migraciones: `python manage.py makemigrations core`
   - Revisar migraciones generadas y aplicarlas: `python manage.py migrate`
   - Probar los endpoints afectados.

3. Si publicas `management.core` como paquete compartido entre proyectos:
   - Versiona y publica (wheel/git tag).
   - Actualiza dependencia en proyectos consumidores y reinicia servicios.

Notas adicionales
-----------------
- Mantén las migraciones bajo control de versiones.
- Si trabajas con PostgreSQL en desarrollo, asegúrate de crear la DB y las credenciales antes de cambiar `DATABASES` en `settings.py`.