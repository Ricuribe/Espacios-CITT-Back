#!/bin/bash
# Setup script for API Gateway

echo "=========================================="
echo "API Gateway Setup"
echo "=========================================="

# Create superuser
echo ""
echo "Creating superuser for admin access..."
python manage.py createsuperuser

# Apply migrations
echo ""
echo "Applying database migrations..."
python manage.py migrate

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run the gateway: python manage.py runserver 8000"
echo "2. Run the backend services on their respective ports:"
echo "   - Management: python manage.py runserver 8001"
echo "   - Repository: python manage.py runserver 8002"
echo "   - Scheduling: python manage.py runserver 8003"
echo ""
echo "Test login endpoint: POST /api/auth/login/"
echo "Use the token from login in Authorization header for other endpoints"
echo ""
