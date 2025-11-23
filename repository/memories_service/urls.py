from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MemoriaViewSet
from .api import DownloadMemoryView, MemoryDetailView, FilterMemoriesView

router = DefaultRouter()
router.register(r'memories', MemoriaViewSet)

urlpatterns = [
    path('memos/', include(router.urls)),
    path('memos/<int:pk>/', MemoryDetailView.as_view(), name='memory-detail'),
    path('memos/download/<int:pk>/', DownloadMemoryView.as_view(), name='download-memory'),
    path('memos/filter/', FilterMemoriesView.as_view(), name='filter-memories'),
]