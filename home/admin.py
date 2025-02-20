from django.contrib import admin
from .models import CustomUser, PostCategory,Post

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(PostCategory)
admin.site.register(Post)
