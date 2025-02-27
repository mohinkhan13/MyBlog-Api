from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import (
    UserSerializer, CategorySerializer, PostSerializer,
    CommentSerializer, ReplySerializer, PostStatsSerializer
)
from .models import CustomUser, PostCategory, Post, Comment, Reply, PostStats
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F, ExpressionWrapper, FloatField
from django.db.models.functions import ExtractWeek, Now
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAdminUser


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['is_superuser'] = user.is_superuser  # Explicitly add to refresh token
    refresh['is_staff'] = user.is_staff
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(email=serializer.validated_data["email"]).exists():
            return Response({"error": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.create_user(**serializer.validated_data)
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "User registered successfully!",
                "user": UserSerializer(user).data,
                "tokens": tokens
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Registration failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        
        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        
        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user).data
        user_data['is_admin'] = user.is_staff
        user_data['is_superuser'] = user.is_superuser  # Add this
        response_data = {
            "user": user_data,
            "tokens": {"access": tokens["access"], "refresh": tokens["refresh"]},
            "redirect": "/admin" if user.is_superuser else "/"  # Update to is_superuser
        }
        from rest_framework_simplejwt.tokens import AccessToken
        access_token = AccessToken(tokens["access"])
        print("Generated Access Token Payload:", access_token.payload)
        return Response(response_data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        auth = JWTAuthentication()
        header = request.headers.get('Authorization')        
        if header:
            try:
                token = header.split()[1]
                validated_token = auth.get_validated_token(token)                
                user = auth.get_user(validated_token)                
            except Exception as e:                
                return Response({"detail": str(e)}, status=401)        
        if not request.user.is_authenticated:
            return Response({"detail": "User not authenticated"}, status=401)
        try:
            user = request.user
            return Response(UserSerializer(user).data)
        except Exception as e:            
            return Response({"detail": str(e)}, status=500)
        
class CategoryViewset(ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]  # Protected

class UserViewset(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Protected

class PostViewset(ModelViewSet):
    serializer_class = PostSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        print(f"User: {user}, Is Authenticated: {user.is_authenticated}, Is Superuser: {user.is_superuser}, Is Staff: {user.is_staff}")
        if user.is_authenticated and user.is_superuser:
            qs = Post.objects.all().order_by('-created_at')
            print("Superuser Posts:", list(qs.values()))  # Debug all posts
            return qs
        qs = Post.objects.filter(status='publish').order_by('-created_at')
        print("Non-Superuser Posts:", list(qs.values()))  # Debug publish posts
        return qs
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)  
    
    def perform_update(self, serializer):
        serializer.save()  

class CommentViewset(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()] 

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReplyViewset(ModelViewSet):
    serializer_class = ReplySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]  # GET ko public karo

    def get_queryset(self):
        queryset = Reply.objects.all()
        comment_id = self.request.query_params.get('comment', None)
        if comment_id is not None:
            queryset = queryset.filter(comment_id=comment_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PostStatsViewset(ModelViewSet):
    queryset = PostStats.objects.all()
    serializer_class = PostStatsSerializer
    permission_classes = [AllowAny]  # Protected

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def post_of_the_week(self, request):
        current_week = ExtractWeek(Now())
        post_of_week = (
            PostStats.objects.annotate(
                engagement_score=ExpressionWrapper(
                    0.2 * F('views') + 0.3 * F('likes') + 0.3 * F('comments') + 0.2 * F('shares'),
                    output_field=FloatField()
                )
            )
            .filter(post__created_at__week=current_week)
            .order_by('-engagement_score')
            .first()
        )

        if not post_of_week:
            post_of_week = (
                PostStats.objects.annotate(
                    engagement_score=ExpressionWrapper(
                        0.2 * F('views') + 0.3 * F('likes') + 0.3 * F('comments') + 0.2 * F('shares'),
                        output_field=FloatField()
                    )
                )
                .order_by('-engagement_score')
                .first()
            )

        if post_of_week:
            serializer = self.get_serializer(post_of_week)
            return Response(serializer.data)
        return Response({"message": "No post found for this week"}, status=status.HTTP_404_NOT_FOUND)