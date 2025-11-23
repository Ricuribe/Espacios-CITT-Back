"""
Configuración centralizada para el endpoint de filtrado de memorias.

Este módulo proporciona una configuración dinámica que se obtiene directamente
del modelo Memoria, evitando duplicación de código y asegurando que los cambios
en el modelo se reflejen automáticamente en el endpoint de filtrado.
"""

from .models import Memoria


def get_valid_fields():
    """
    Obtiene la configuración de campos válidos para filtrado.
    
    Esta función construye dinámicamente la configuración basada en los campos
    del modelo Memoria, asegurando que cualquier cambio en el modelo se refleje
    automáticamente.
    
    Returns:
        dict: Diccionario con la configuración de campos válidos.
              Formato: {'nombre_campo': 'tipo_validacion'}
    """
    return {
        'id_memo': 'integer',
        'titulo': 'string',
        'profesor': 'string',
        'descripcion': 'string_contains',
        'escuela': 'choice',
        'carrera': 'choice',
        'entidad_involucrada': 'string',
        'tipo_entidad': 'string',
        'tipo_memoria': 'string',
        'fecha_inicio': 'date',
        'fecha_termino': 'date',
        'fecha_subida': 'date',
    }


def get_career_choices():
    """
    Obtiene las opciones de carrera directamente del modelo.
    
    Esta función obtiene las choices del campo 'carrera' del modelo Memoria,
    asegurando que el endpoint siempre tenga las opciones actualizadas.
    
    Returns:
        dict: Diccionario con las opciones de carrera.
              Formato: {'CODIGO': 'Descripción'}
    
    Examples:
        - choices = get_career_choices()
        - choices['INGINFO']
        'Ingeniería en Informática'
    """
    # Obtener el campo 'carrera' del modelo
    carrera_field = Memoria._meta.get_field('carrera')
    
    # Convertir las choices a un diccionario
    choices_dict = {}
    for value, label in carrera_field.choices:
        choices_dict[value] = label
    
    return choices_dict


def get_escuela_choices():
    """
    Obtiene las opciones de 'escuela' directamente del modelo.

    Returns:
        dict: Diccionario con las opciones de escuela. Formato: {'CODIGO': 'Descripción'}
    """
    escuela_field = Memoria._meta.get_field('escuela')
    choices_dict = {}
    for value, label in escuela_field.choices:
        choices_dict[value] = label
    return choices_dict


def get_detalle_valid_fields():
    """
    Retorna los campos válidos del modelo relacionado `MemoriaDetalle` que
    pueden usarse para filtrar desde el endpoint principal.

    Formato: {'nombre_campo_detalle': 'tipo_validacion'}
    Tipos soportados: 'rut', 'string'
    """
    return {
        'rut_estudiante': 'rut',
        'nombre_estudiante': 'string',
        'apellido_estudiante': 'string',
        'segundo_nombre_estudiante': 'string',
        'segundo_apellido_estudiante': 'string',
    }


def get_all_filter_config():
    """
    Obtiene toda la configuración de filtrado de forma centralizada.
    
    Returns:
        dict: Diccionario con 'valid_fields' y 'career_choices'
    """
    return {
        'valid_fields': get_valid_fields(),
        'career_choices': get_career_choices(),
        'escuela_choices': get_escuela_choices(),
        'detalle_fields': get_detalle_valid_fields(),
    }
