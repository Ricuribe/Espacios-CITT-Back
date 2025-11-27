from django.urls import path, re_path
from . import views

app_name = 'gateway_service'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/me/', views.UserDetailView.as_view(), name='user-detail'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/refresh/', views.TokenRefreshView.as_view(), name='token-refresh'),

    # Management Service Proxy (workspaces and schedules)
    re_path(r'^manage/(?P<path>.*)', views.ManagementProxyView.as_view(), name='manage-proxy'),

    # Repository Service Proxy (memories)
    re_path(r'^memos/(?P<path>.*)', views.RepositoryProxyView.as_view(), name='memos-proxy'),

    # Scheduling Service Proxy (events)
    re_path(r'^event/(?P<path>.*)', views.SchedulingProxyView.as_view(), name='event-proxy'),
]
