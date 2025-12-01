from .base import *
import os

DEBUG = True 
ALLOWED_HOSTS = ['*']

#! Base de datos AWS RDS (Lee del .env)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME_MEMOS'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': '5432',
    }
}

#! CONFIGURACIÓN DE S3
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = 'us-east-1' # Tu región de AWS Academy

# Configuraciones para que los archivos sean públicos y legibles
AWS_S3_Object_Ownership = 'BucketOwnerPreferred'
AWS_S3_FILE_OVERWRITE = False # No sobreescribir archivos con el mismo nombre
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False # Para que la URL de la imagen sea limpia y permanente

# Decirle a Django que use S3 para guardar archivos (Media)
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}