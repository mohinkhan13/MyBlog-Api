from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewset, CategoryViewset, PostViewset,
    CommentViewset, ReplyViewset, PostStatsViewset,
    LoginView, LogoutView, CurrentUserView, RegisterView
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
    
    # 🔹 Authentication Routes
    path('login/', LoginView.as_view(), name='login'),
    path("register/", RegisterView.as_view(), name="register"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('current-user/', CurrentUserView.as_view(), name='current-user'),
]
