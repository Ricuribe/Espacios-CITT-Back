from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.response import Response
from django.http import HttpResponse
import requests
from django.conf import settings
from .serializers import UserLoginSerializer, UserRegisterSerializer, UserSerializer


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class LoginView(APIView):
    """
    Endpoint de inicio de sesión que devuelve tokens JWT.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    """
    Endpoint de registro para crear nuevos usuarios. NO CREA TOKENS, SOLO EL USUARIO
    """
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UserDetailView(APIView):
    """
    Obtener los detalles del usuario actual.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """
    Endpoint para refrescar el token de acceso usando un token de refresco.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Token de refresco requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            return Response(
                {'access': access_token},
                status=status.HTTP_200_OK
            )
        except TokenError as e:
            return Response(
                {'error': 'Token inválido o expirado'},
                status=status.HTTP_401_UNAUTHORIZED
            )

class LogoutView(APIView):
    """
    Endpoint de cierre de sesión que invalida el token de refresco.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Token de refresco requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create RefreshToken instance and add to blacklist
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'detail': 'Sesión cerrada exitosamente'},
                status=status.HTTP_200_OK
            )
        except TokenError as e:
            return Response(
                {'error': 'Token inválido o expirado'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': f'Error al cerrar sesión: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================================
# HELPER FUNCTION FOR PROXY
# ============================================================================

def forward_request_to_backend(request, base_url, path):
    """
    Proxy Universal: Maneja JSON, Multipart (Archivos) y Descargas Binarias.
    """
    # ------------------------------------------------------------------
    # 1. Construcción y Limpieza de URL (Tu fix anterior)
    # ------------------------------------------------------------------
    url = f"{base_url}/{path}"
    if '?' in url:
        url = url.split('?')[0]
    
    # Asegurar slash final para evitar redirecciones POST -> GET
    if not url.endswith('/'):
        url += '/'

    # ------------------------------------------------------------------
    # 2. Preparación de Headers
    # ------------------------------------------------------------------
    # Copiamos headers del cliente, pero filtramos los peligrosos
    headers = {}
    for k, v in request.headers.items():
        if k.lower() not in ['host', 'content-length', 'connection']:
            headers[k] = v

    # CRÍTICO PARA UPLOADS: Si es multipart, ELIMINAMOS el Content-Type.
    # La librería 'requests' debe generar su propio boundary automáticamente.
    # Si dejamos el original, el backend no podrá parsear el archivo.
    if 'multipart/form-data' in request.content_type:
        headers.pop('Content-Type', None)
        headers.pop('content-type', None)

    # ------------------------------------------------------------------
    # 3. Preparación del Payload (Archivos vs JSON)
    # ------------------------------------------------------------------
    files = None
    data = None
    json_payload = None

    try:
        if 'multipart/form-data' in request.content_type:
            # Caso UPLOAD: Separamos archivos de datos normales
            # request.FILES contiene los archivos reales
            # request.POST contiene los campos de texto
            files = {}
            # Convertir Django UploadedFiles a formato compatible con requests
            for key, file_obj in request.FILES.items():
                # requests espera: (filename, file_object, content_type)
                files[key] = (file_obj.name, file_obj, file_obj.content_type)
            
            data = request.POST # Datos del formulario
        else:
            # Caso JSON/Normal
            json_payload = request.data

        # ------------------------------------------------------------------
        # 4. Envío de la Solicitud
        # ------------------------------------------------------------------
        method_map = {
            'GET': requests.get,
            'POST': requests.post,
            'PUT': requests.put,
            'PATCH': requests.patch,
            'DELETE': requests.delete,
        }
        method = request.method.upper()

        # Configuración común para requests
        req_kwargs = {
            'url': url,
            'headers': headers,
            'params': request.query_params,
            'timeout': 30  # Aumentamos timeout para subidas de archivos
        }

        # Inyectar payload según el tipo
        if method in ['POST', 'PUT', 'PATCH']:
            if files:
                req_kwargs['files'] = files
                req_kwargs['data'] = data
            else:
                req_kwargs['json'] = json_payload

        # Ejecutar la petición
        response = method_map[method](**req_kwargs)

        # ------------------------------------------------------------------
        # 5. Manejo de Respuesta (Descargas vs JSON)
        # ------------------------------------------------------------------
        content_type_resp = response.headers.get('Content-Type', '').lower()

        # Si el backend devuelve JSON, lo procesamos como siempre
        if 'application/json' in content_type_resp:
            try:
                return Response(response.json(), status=response.status_code)
            except ValueError:
                return Response(response.content, status=response.status_code)

        # CASO DESCARGA (PDF, Imagen, Zip): Devolvemos el binario crudo
        # Usamos HttpResponse de Django en lugar de Response de DRF para streams/binarios
        django_response = HttpResponse(
            response.content, 
            status=response.status_code, 
            content_type=content_type_resp
        )
        
        # Preservar header importante para descargas (nombre del archivo)
        if 'Content-Disposition' in response.headers:
            django_response['Content-Disposition'] = response.headers['Content-Disposition']
            
        return django_response

    except requests.exceptions.ConnectionError:
        return Response({'error': 'Servicio no disponible'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# PROXY VIEWS - MANAGEMENT SERVICE
# ============================================================================

class ManagementProxyView(APIView):
    """
    Proxy para los endpoints del servicio de gestión.
    Reenvía las solicitudes al servicio de gestión definido en MANAGEMENT_SERVICE_URL.
    """
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        path = kwargs.get('path', '')
        request.method_name = request.method.lower()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, path=''):
        return forward_request_to_backend(request, settings.MANAGEMENT_SERVICE_URL, path)

    def post(self, request, path=''):
        return forward_request_to_backend(request, settings.MANAGEMENT_SERVICE_URL, path)

    def put(self, request, path=''):
        return forward_request_to_backend(request, settings.MANAGEMENT_SERVICE_URL, path)

    def patch(self, request, path=''):
        return forward_request_to_backend(request, settings.MANAGEMENT_SERVICE_URL, path)

    def delete(self, request, path=''):
        return forward_request_to_backend(request, settings.MANAGEMENT_SERVICE_URL, path)


# ============================================================================
# PROXY VIEWS - REPOSITORY SERVICE
# ============================================================================

class RepositoryProxyView(APIView):
    """
    Proxy para los endpoints del servicio de repositorio.
    Reenvía las solicitudes al servicio de repositorio definido en REPOSITORY_SERVICE_URL.
    """
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        path = kwargs.get('path', '')
        request.method_name = request.method.lower()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, path=''):
        return forward_request_to_backend(request, settings.REPOSITORY_SERVICE_URL, path)

    def post(self, request, path=''):
        return forward_request_to_backend(request, settings.REPOSITORY_SERVICE_URL, path)

    def put(self, request, path=''):
        return forward_request_to_backend(request, settings.REPOSITORY_SERVICE_URL, path)

    def patch(self, request, path=''):
        return forward_request_to_backend(request, settings.REPOSITORY_SERVICE_URL, path)

    def delete(self, request, path=''):
        return forward_request_to_backend(request, settings.REPOSITORY_SERVICE_URL, path)


# ============================================================================
# PROXY VIEWS - SCHEDULING SERVICE
# ============================================================================

class SchedulingProxyView(APIView):
    """
    Proxy para los endpoints del servicio de eventos (scheduling).
    Reenvía las solicitudes al servicio de scheduling definido en SCHEDULING_SERVICE_URL.

    Soporta una "whitelist" (configurable mediante la variable de settings
    `SCHEDULING_PUBLIC_PATHS`) con rutas públicas que no requieren autenticación.
    """
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        # Guardamos la ruta proxy para que get_permissions pueda decidir
        # si este endpoint es público o requiere autenticación.
        path = kwargs.get('path', '')
        self.proxy_path = path or ''
        request.method_name = request.method.lower()
        return super().dispatch(request, *args, **kwargs)

    def get_permissions(self):
        # Rutas públicas configurables desde settings. Por defecto:
        # 'future-activity' y 'scheduled-events'
        public_paths = getattr(settings, 'SCHEDULING_PUBLIC_PATHS', [
            'future-activity',
            'scheduled-events',
        ])

        # Normalizamos la ruta y comprobamos si comienza con alguna pública
        path = getattr(self, 'proxy_path', '').lstrip('/')
        for p in public_paths:
            if path == p or path.startswith(p + '/') or path.startswith(p + '?'):
                return [AllowAny()]

        return [IsAuthenticated()]

    def get(self, request, path=''):
        return forward_request_to_backend(request, settings.SCHEDULING_SERVICE_URL, path)

    def post(self, request, path=''):
        return forward_request_to_backend(request, settings.SCHEDULING_SERVICE_URL, path)

    def put(self, request, path=''):
        return forward_request_to_backend(request, settings.SCHEDULING_SERVICE_URL, path)

    def patch(self, request, path=''):
        return forward_request_to_backend(request, settings.SCHEDULING_SERVICE_URL, path)

    def delete(self, request, path=''):
        return forward_request_to_backend(request, settings.SCHEDULING_SERVICE_URL, path)
