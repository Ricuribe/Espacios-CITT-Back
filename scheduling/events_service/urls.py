from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, get_future_activity, get_future_activity_by_workspace

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')

urlpatterns = [
    path('event/', include(router.urls)),
    path('future-activity/', get_future_activity, name='future-activity'),
    path('future-activity/<int:workspace_id>/', get_future_activity_by_workspace, name='future-activity-by-workspace'),
]