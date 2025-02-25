from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewset, CategoryViewset, PostViewset,
    CommentViewset, ReplyViewset, PostStatsViewset
)

# 🔹 Registering All Viewsets
router = DefaultRouter()
router.register(r'users', UserViewset, basename='user')
router.register(r'categories', CategoryViewset, basename='category')
router.register(r'posts', PostViewset, basename='post')
router.register(r'comments', CommentViewset, basename='comment')
router.register(r'replies', ReplyViewset, basename='reply')
router.register(r'post-stats', PostStatsViewset, basename='poststats')

# 🔹 Including Routes
urlpatterns = [
    path('', include(router.urls)),
]
