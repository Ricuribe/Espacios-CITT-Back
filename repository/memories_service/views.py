from rest_framework import viewsets
from .models import Memoria
from .serializers import MemoriaSerializer

class MemoriaViewSet(viewsets.ModelViewSet):
    queryset = Memoria.objects.all()
    serializer_class = MemoriaSerializer
    