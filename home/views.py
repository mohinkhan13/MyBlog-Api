from rest_framework.viewsets import ModelViewSet
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

# 🔹 Category Viewset
class CategoryViewset(ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = CategorySerializer


# 🔹 User Viewset
class UserViewset(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer


# 🔹 Post Viewset
class PostViewset(ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    parser_classes = (MultiPartParser, FormParser)


# 🔹 Comment Viewset
class CommentViewset(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    lookup_field = 'id'

# 🔹 Reply Viewset
class ReplyViewset(ModelViewSet):
    serializer_class = ReplySerializer
    lookup_field = 'id'

    def get_queryset(self):
        queryset = Reply.objects.all()
        comment_id = self.request.query_params.get('comment', None)
        if comment_id is not None:
            queryset = queryset.filter(comment_id=comment_id)
        return queryset

# 🔹 PostStats Viewset
class PostStatsViewset(ModelViewSet):
    queryset = PostStats.objects.all()
    serializer_class = PostStatsSerializer

    lookup_field = 'id'

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    
    @action(detail=False, methods=['get'])
    def post_of_the_week(self, request):
        """Post of the Week - Based on Engagement Score"""
        current_week = ExtractWeek(Now())

        post_of_week = (
            PostStats.objects.annotate(
                engagement_score=ExpressionWrapper(
                    0.2 * F('views') + 0.3 * F('likes') + 0.3 * F('comments') + 0.2 * F('shares'),
                    output_field=FloatField()
                )
            )
            .filter(post__created_at__week=current_week)  # Filter by current week
            .order_by('-engagement_score')  # Order by engagement score
            .first()  # Get highest engagement score post
        )

        if not post_of_week:
            post_of_week = (
                PostStats.objects.annotate(
                    engagement_score=ExpressionWrapper(
                        0.2 * F('views') + 0.3 * F('likes') + 0.3 * F('comments') + 0.2 * F('shares'),
                        output_field=FloatField()
                    )
                )
                .order_by('-engagement_score')  # ✅ Overall highest engagement post
                .first()
            )

        if post_of_week:
            serializer = self.get_serializer(post_of_week)
            return Response(serializer.data)
        return Response({"message": "No post found for this week"}, status=404)
