from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, get_future_activity

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')

urlpatterns = [
    path('event/', include(router.urls)),
    path('future-activity/', get_future_activity, name='future-activity'),
]