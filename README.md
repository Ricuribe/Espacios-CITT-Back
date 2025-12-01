# Espacios-CITT-Back

Backend del proyecto "Gestión de espacios y repositorio de memorias CITT"

<small> Proyecto diseñado para su funcionamiento de forma local o con base de datos en RDS y gestor de archivos S3 en AWS

## 📚 Documentación

**[👉 Ve a la carpeta `docs/` para la documentación completa](docs/INDEX.md)**

Toda la documentación, guías, ejemplos y arquitectura está organizada en la carpeta `docs/`.
Comienza con [docs/START.md](docs/START.md) si es tu primer contacto.

---

## ⚙️ Requisitos Previos

Tener instalado **PostgreSQL 18** antes de ejecutar el backend

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

**Para este punto debería estar creada las bases de datos "espaciosCITT" y "memoriasCITT" en Postgres antes de esta parte, en AWS, ya están creadas**

**RECORDATORIO: Los archivos de entorno .env deben ir ubicado en sus respectivas carpetas del backend (junto a manage.py)**

-----

## ☁️ Guía de Ejecución: Arquitectura Híbrida (Local vs AWS)

Este proyecto ha sido refactorizado para soportar dos modos de ejecución mediante **Settings Modulares**.

### 📋 Conceptos Clave

  * **Modo LOCAL (`.local`):**

      * **Base de Datos:** PostgreSQL instalada en tu máquina (`localhost`).
      * **Archivos:** Se guardan en la carpeta `media/` de tu disco duro.
      * **Uso:** Desarrollo diario, pruebas offline o cuando AWS Academy está apagado.

  * **Modo PRODUCCIÓN (`.production`):**

      * **Base de Datos:** AWS RDS (PostgreSQL en la nube).
      * **Archivos:** AWS S3 (Bucket en la nube).
      * **Uso:** Pruebas de integración real, demostraciones y validación de despliegue.

-----

### 🛠️ Requisitos Previos

1.  **Nuevas Dependencias:** Asegúrate de instalar las librerías de soporte para AWS:
    ```bash
    pip install boto3 django-storages
    ```
2.  **Archivos .env:** Cada carpeta de servicio (`api_gateway`, `management`, `repository`, `scheduling`) debe tener su propio archivo `.env` con las credenciales correspondientes.

-----

### 🚀 Comandos de Ejecución por Terminal

Para cambiar entre modos, definimos la variable de entorno `DJANGO_SETTINGS_MODULE` antes de correr el servidor.

#### 1\. API Gateway (Puerto 8000)

*Ubicación: `cd api_gateway`*

| Terminal | Comando para MODO LOCAL | Comando para MODO AWS (PROD) |
| :--- | :--- | :--- |
| **PowerShell** | `$env:DJANGO_SETTINGS_MODULE="api_gateway.settings.local"; python manage.py runserver 8000` | `$env:DJANGO_SETTINGS_MODULE="api_gateway.settings.production"; python manage.py runserver 8000` |
| **Git Bash** | `export DJANGO_SETTINGS_MODULE=api_gateway.settings.local && python manage.py runserver 8000` | `export DJANGO_SETTINGS_MODULE=api_gateway.settings.production && python manage.py runserver 8000` |
| **CMD** | `set DJANGO_SETTINGS_MODULE=api_gateway.settings.local & python manage.py runserver 8000` | `set DJANGO_SETTINGS_MODULE=api_gateway.settings.production & python manage.py runserver 8000` |

#### 2\. Management Service (Puerto 8001)

*Ubicación: `cd management`*

| Terminal | Comando para MODO LOCAL | Comando para MODO AWS (PROD) |
| :--- | :--- | :--- |
| **PowerShell** | `$env:DJANGO_SETTINGS_MODULE="management.settings.local"; python manage.py runserver 8001` | `$env:DJANGO_SETTINGS_MODULE="management.settings.production"; python manage.py runserver 8001` |
| **Git Bash** | `export DJANGO_SETTINGS_MODULE=management.settings.local && python manage.py runserver 8001` | `export DJANGO_SETTINGS_MODULE=management.settings.production && python manage.py runserver 8001` |
| **CMD** | `set DJANGO_SETTINGS_MODULE=management.settings.local & python manage.py runserver 8001` | `set DJANGO_SETTINGS_MODULE=management.settings.production & python manage.py runserver 8001` |

#### 3\. Repository Service (Puerto 8002) - *¡Usa S3\!*

*Ubicación: `cd repository`*

| Terminal | Comando para MODO LOCAL | Comando para MODO AWS (PROD) |
| :--- | :--- | :--- |
| **PowerShell** | `$env:DJANGO_SETTINGS_MODULE="repository.settings.local"; python manage.py runserver 8002` | `$env:DJANGO_SETTINGS_MODULE="repository.settings.production"; python manage.py runserver 8002` |
| **Git Bash** | `export DJANGO_SETTINGS_MODULE=repository.settings.local && python manage.py runserver 8002` | `export DJANGO_SETTINGS_MODULE=repository.settings.production && python manage.py runserver 8002` |
| **CMD** | `set DJANGO_SETTINGS_MODULE=repository.settings.local & python manage.py runserver 8002` | `set DJANGO_SETTINGS_MODULE=repository.settings.production & python manage.py runserver 8002` |

#### 4\. Scheduling Service (Puerto 8003)

*Ubicación: `cd scheduling`*

| Terminal | Comando para MODO LOCAL | Comando para MODO AWS (PROD) |
| :--- | :--- | :--- |
| **PowerShell** | `$env:DJANGO_SETTINGS_MODULE="scheduling.settings.local"; python manage.py runserver 8003` | `$env:DJANGO_SETTINGS_MODULE="scheduling.settings.production"; python manage.py runserver 8003` |
| **Git Bash** | `export DJANGO_SETTINGS_MODULE=scheduling.settings.local && python manage.py runserver 8003` | `export DJANGO_SETTINGS_MODULE=scheduling.settings.production && python manage.py runserver 8003` |
| **CMD** | `set DJANGO_SETTINGS_MODULE=scheduling.settings.local & python manage.py runserver 8003` | `set DJANGO_SETTINGS_MODULE=scheduling.settings.production & python manage.py runserver 8003` |

-----

### ⚠️ Notas Importantes (AWS Academy)

1.  **Credenciales Caducas:** Las credenciales de AWS Academy (`AWS_ACCESS_KEY`, `SESSION_TOKEN`) son temporales. Si obtienes errores de conexión (`AuthFailure` o `SignatureDoesNotMatch`), debes ir a la consola del curso, copiar las nuevas credenciales y pegarlas en el `.env` de cada servicio.
2.  **Migraciones en la Nube:** La primera vez que uses el modo producción (o si reiniciaste la BD en AWS), debes crear las tablas allá:
    ```bash
    # Ejemplo en PowerShell
    $env:DJANGO_SETTINGS_MODULE="management.settings.production"
    python manage.py migrate
    ```
3.  **Datos Separados:** Recuerda que lo que guardas en **Local** NO se ve en **Producción** y viceversa. Son bases de datos totalmente distintas.
