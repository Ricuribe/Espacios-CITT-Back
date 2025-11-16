# Configuration for API Gateway
# Edit these values according to your environment

# Backend Services URLs
# These should point to the actual running services
MANAGEMENT_SERVICE_URL = 'http://localhost:8001/api'
REPOSITORY_SERVICE_URL = 'http://localhost:8002/api'
SCHEDULING_SERVICE_URL = 'http://localhost:8003/api'

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME = 24  # hours
JWT_REFRESH_TOKEN_LIFETIME = 7  # days

# CORS Configuration
ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000',
]

# Request timeout (in seconds)
REQUEST_TIMEOUT = 10
