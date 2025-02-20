from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewset, CategoryViewset, PostViewset


router = DefaultRouter()
router.register(r'users', UserViewset, basename='user')
router.register(r'categories', CategoryViewset, basename='category')
router.register(r'posts', PostViewset, basename='post')

urlpatterns = [
    path('', include(router.urls)),
]
