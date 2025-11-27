from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import requests
from django.conf import settings
from .serializers import UserLoginSerializer, UserRegisterSerializer, UserSerializer


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class LoginView(APIView):
    """
    Login endpoint that returns JWT tokens.
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
    Register endpoint to create new users.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    """
    Get current user details.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout endpoint that invalidates the refresh token.
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
    Generic function to forward requests to backend services.
    
    Args:
        request: Django request object
        base_url: Base URL of the backend service
        path: Relative path to forward
        
    Returns:
        Response object with forwarded data or error message
    """
    url = f"{base_url}/{path}".rstrip('/')
    
    # Remove query parameters from URL if they exist
    if '?' in url:
        url = url.split('?')[0]
    
    try:
        # Prepare headers to forward
        headers = {}
        
        # Map request methods to requests library functions
        method_map = {
            'GET': requests.get,
            'POST': requests.post,
            'PUT': requests.put,
            'PATCH': requests.patch,
            'DELETE': requests.delete,
        }
        
        method = request.method.upper()
        
        if method not in method_map:
            return Response(
                {'error': f'Método {method} no permitido'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        
        # Make the request
        if method == 'GET':
            response = requests.get(url, params=request.query_params, headers=headers, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            # For POST, PUT, PATCH - send the body
            try:
                response = method_map[method](url, json=request.data, headers=headers, timeout=10)
            except (ValueError, TypeError):
                # If body is not JSON, try as raw data
                response = method_map[method](url, data=request.data, headers=headers, timeout=10)
        
        # Try to parse response as JSON
        try:
            response_data = response.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            # If response is not JSON, return as text
            response_data = {'detail': response.text or 'No content'}
        
        return Response(response_data, status=response.status_code)
    
    except requests.exceptions.ConnectionError:
        return Response(
            {'error': 'No se puede conectar al servicio backend'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except requests.exceptions.Timeout:
        return Response(
            {'error': 'Timeout conectando al servicio backend'},
            status=status.HTTP_504_GATEWAY_TIMEOUT
        )
    except Exception as e:
        return Response(
            {'error': f'Error en gateway: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# PROXY VIEWS - MANAGEMENT SERVICE
# ============================================================================

class ManagementProxyView(APIView):
    """
    Proxy for management service endpoints.
    Forwards requests to the management service at MANAGEMENT_SERVICE_URL.
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
    Proxy for repository service endpoints.
    Forwards requests to the repository service at REPOSITORY_SERVICE_URL.
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
    Proxy for scheduling service endpoints.
    Forwards requests to the scheduling service at SCHEDULING_SERVICE_URL.
    """
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        path = kwargs.get('path', '')
        request.method_name = request.method.lower()
        return super().dispatch(request, *args, **kwargs)

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
