from rest_framework import viewsets
from .models import UserAccount
from .serializers import UserAccountSerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = UserAccount.objects.all()
    serializer_class = UserAccountSerializer
