from rest_framework.viewsets import ModelViewSet
from .serializers import UserSerializer, CategorySerializer, PostSerializer
from .models import CustomUser,PostCategory, Post
from rest_framework.parsers import MultiPartParser, FormParser

class CategoryViewset(ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = CategorySerializer

class UserViewset(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

class PostViewset(ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    parser_classes = (MultiPartParser, FormParser)