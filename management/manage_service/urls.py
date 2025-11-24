from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkspaceViewSet, EventsManagementViewSet
from .api import UserLoginView


router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'events-manage', EventsManagementViewSet, basename='event-manage')

urlpatterns = [
    path('manage/', include(router.urls)),
    path('user/login/', UserLoginView.as_view(), name='user-login'),
]