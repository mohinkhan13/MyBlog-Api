from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import (
    UserSerializer, CategorySerializer, PostSerializer,
    CommentSerializer, ReplySerializer, PostStatsSerializer, ContactSerializer, NewsletterSerializer
)
from .models import CustomUser, PostCategory, Post, Comment, Reply, PostStats, Contact, NewsLetter
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
from rest_framework import permissions
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['is_superuser'] = user.is_superuser
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
        try:
            user = CustomUser.objects.create_user(**serializer.validated_data)
            tokens = get_tokens_for_user(user)
            logger.info(f"User {user.email} registered successfully")
            return Response({
                "message": "User registered successfully!",
                "user": UserSerializer(user).data,
                "tokens": tokens
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
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
        user_data['is_superuser'] = user.is_superuser
        response_data = {
            "user": user_data,
            "tokens": {"access": tokens["access"], "refresh": tokens["refresh"]},
            "redirect": "/admin" if user.is_superuser or user.is_staff else "/"
        }
        logger.info(f"User {user.email} logged in successfully")
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
            logger.info(f"User {request.user.email} logged out successfully")
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            return Response(UserSerializer(user).data)
        except Exception as e:
            logger.error(f"Current user fetch failed: {str(e)}")
            return Response({"detail": str(e)}, status=500)

class CategoryViewset(ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class UserViewset(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class PostViewset(ModelViewSet):
    serializer_class = PostSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        print(f"User: {user}, Is Authenticated: {user.is_authenticated}, Is Superuser: {user.is_superuser}")
        if user.is_authenticated and user.is_superuser:
            return Post.objects.all().order_by('-created_at')
        return Post.objects.filter(status='publish').order_by('-created_at')
    
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
        with transaction.atomic():
            comment = serializer.save(user=self.request.user)
            # Increment PostStats comments count
            post_stats, created = PostStats.objects.get_or_create(post=comment.post)
            post_stats.comments = F('comments') + 1
            post_stats.save(update_fields=['comments'])
            logger.info(f"Comment created for post {comment.post.title}, stats updated")

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            comment = self.get_object()
            post_stats = PostStats.objects.get(post=comment.post)
            post_stats.comments = F('comments') - 1
            post_stats.save(update_fields=['comments'])
            logger.info(f"Comment deleted for post {comment.post.title}, stats updated")
            return super().destroy(request, *args, **kwargs)

class ReplyViewset(ModelViewSet):
    serializer_class = ReplySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

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
    permission_classes = [AllowAny]

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
   
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_like(self, request, pk=None):
        post_stat = self.get_object()
        user = request.user
        if user in post_stat.liked_by.all():
            post_stat.liked_by.remove(user)
            post_stat.likes = max(0, post_stat.likes - 1)
        else:
            post_stat.liked_by.add(user)
            post_stat.likes += 1
        post_stat.save()
        serializer = self.get_serializer(post_stat)
        return Response(serializer.data)
    
class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    # def list(self, request, *args, **kwargs):
    #     return Response({"message": "GET method not allowed"}, status=status.HTTP_403_FORBIDDEN)

    # def retrieve(self, request, *args, **kwargs):
    #     return Response({"message": "GET method not allowed"}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        return Response({"message": "PATCH/PUT method not allowed"}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        return Response({"message": "DELETE method not allowed"}, status=status.HTTP_403_FORBIDDEN)

class NewsLetterViewSet(ModelViewSet):
    queryset = NewsLetter.objects.all()
    serializer_class = NewsletterSerializer

    def get_permissions(self):
        if self.action in ['create', 'partial_update']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    # def list(self, request, *args, **kwargs):
    #     return Response({"message": "GET method not allowed"}, status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, *args, **kwargs):
        return Response({"message": "GET method not allowed"}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        return Response({"message": "DELETE method not allowed"}, status=status.HTTP_403_FORBIDDEN)