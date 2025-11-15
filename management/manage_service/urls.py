from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkspaceViewSet
from .api import UserLoginView


router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')

urlpatterns = [
    path('manage/', include(router.urls)),
    path('user/login/', UserLoginView.as_view(), name='user-login'),
]