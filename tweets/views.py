from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import CreateTweetSerializer, RetrieveTweetSerializer
from .models import Tweet
from .permissions import IsAuthorOrReadOnly

# Create your views here.


class ListCreateTweetAPIView(generics.ListCreateAPIView):
    queryset = Tweet.objects.all()
    serializer_class = CreateTweetSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RetrieveDeleteTweetAPIView(generics.RetrieveDestroyAPIView):
    queryset = Tweet.objects.all()
    serializer_class = RetrieveTweetSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
