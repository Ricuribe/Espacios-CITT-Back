#!/bin/bash
# Comandos principales del API Gateway

# ============================================================================
# INSTALACIÓN Y CONFIGURACIÓN
# ============================================================================

# Activar virtual environment
source /c/Dev/CITTEsp-back/.venv/Scripts/activate

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
cd /c/Dev/CITTEsp-back/api_gateway
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# ============================================================================
# INICIAR SERVICIOS
# ============================================================================

# Gateway (Puerto 8000) - Terminal 1
python manage.py runserver 8000

# Management Service (Puerto 8001) - Terminal 2
cd /c/Dev/CITTEsp-back/management
python manage.py runserver 8001

# Repository Service (Puerto 8002) - Terminal 3
cd /c/Dev/CITTEsp-back/repository
python manage.py runserver 8002

# Scheduling Service (Puerto 8003) - Terminal 4
cd /c/Dev/CITTEsp-back/scheduling
python manage.py runserver 8003

# ============================================================================
# TESTING
# ============================================================================

# Ejecutar todos los tests
cd /c/Dev/CITTEsp-back/api_gateway
python manage.py test gateway_service.tests -v 2

# Ejecutar test específico
python manage.py test gateway_service.tests.AuthenticationTestCase.test_user_registration -v 2

# ============================================================================
# ADMIN PANEL
# ============================================================================

# Acceder a: http://localhost:8000/admin/

# ============================================================================
# ENDPOINTS DE PRUEBA CON CURL
# ============================================================================

# 1. REGISTRAR USUARIO
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password2": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Guardar el token: TOKEN="<access_token>"

# 2. LOGIN
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'

# 3. OBTENER DATOS DEL USUARIO
TOKEN="<your_token>"
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer $TOKEN"

# 4. LISTAR WORKSPACES (Management Service)
curl -X GET http://localhost:8000/api/manage/workspaces/ \
  -H "Authorization: Bearer $TOKEN"

# 5. LISTAR MEMORIAS (Repository Service)
curl -X GET http://localhost:8000/api/memos/ \
  -H "Authorization: Bearer $TOKEN"

# 6. LISTAR EVENTOS (Scheduling Service)
curl -X GET http://localhost:8000/api/events/ \
  -H "Authorization: Bearer $TOKEN"

# ============================================================================
# HERRAMIENTAS ÚTILES
# ============================================================================

# Ver logs en tiempo real
python manage.py runserver 8000 --verbosity=2

# Limpiar base de datos y recrear
python manage.py flush

# Crear backup de la BD
cp db.sqlite3 db.sqlite3.backup

# Ver SQL de una migración
python manage.py sqlmigrate auth 0001

# Validar modelos sin aplicar
python manage.py migrate --plan

# ============================================================================
# DESARROLLO
# ============================================================================

# Shell interactivo Django
python manage.py shell

# Ejecutar comando Python en shell
python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.all())"

# Hacer migraciones (si hay cambios en models)
python manage.py makemigrations

# Ver migraciones pendientes
python manage.py showmigrations

# Linter (si está instalado)
flake8 gateway_service/

# ============================================================================
# ACTUALIZACIÓN DE DEPENDENCIAS
# ============================================================================

# Ver actualizaciones disponibles
pip list --outdated

# Actualizar paquete específico
pip install --upgrade djangorestframework-simplejwt

# Generar nuevos requirements
pip freeze > requirements.txt

# ============================================================================
# VARIABLES DE ENTORNO (PRODUCCIÓN)
# ============================================================================

# Copiar template
cp .env.example .env

# Editar .env con tus valores
# Luego en settings.py:
# import os
# from dotenv import load_dotenv
# load_dotenv()
# SECRET_KEY = os.getenv('SECRET_KEY')
