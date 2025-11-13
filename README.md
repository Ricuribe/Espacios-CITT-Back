# Espacios-CITT-Back

Backend del proyecto "Gestión de espacios y repositorio de memorias CITT"

### Tener instalado PostgreSQL 18 antes de ejecutar el backend

Dentro de la carpeta del proyecto:

Crear entorno:
```bash
python -m venv nombre-del-entorno
```
Ejecutar entorno:
```bash
.\nombre-del-entorno\Scripts\activate
```
Instala los paquetes necesarios:

*Asegurarse de haber cambiado la ruta del paquete editable (marcado como -e) en el archivo requirements.txt en base a la ubicación del proyecto en tu ordenador*

```bash
pip install -r requirements.txt
```

**Tener creada la base de datos "espaciosCITT" en Postgres antes de esta parte**

Ir a la carpeta management y ejecutar:

```bash
python manage.py makemigrations
python manage.py migrate
```

Ejecutar los módulos del backend (dentro de cada carpeta):

```bash
python manage.py runserver
```
