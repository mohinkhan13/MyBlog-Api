from django.contrib import admin
from .models import CustomUser, PostCategory,Post, PostStats , Comment , Reply , Contact , NewsLetter, ActivityLog

# Register your models here.
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id','email', 'is_staff', 'is_superuser')
admin.site.register(CustomUser, CustomUserAdmin)

class PostCategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'slug')
admin.site.register(PostCategory, PostCategoryAdmin)

class PostAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'category', 'status', 'created_at', 'updated_at')
admin.site.register(Post, PostAdmin)
class PostStatsAdmin(admin.ModelAdmin):
    list_display = ('id','post', 'views', 'likes', 'comments', 'shares')
admin.site.register(PostStats, PostStatsAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('id','post', 'user', 'content', 'created_at')
admin.site.register(Comment, CommentAdmin)

class ReplyAdmin(admin.ModelAdmin):
    list_display = ('id','comment', 'user', 'content', 'created_at')
admin.site.register(Reply, ReplyAdmin)


class ContactAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'email', 'subject', 'message', 'created_at')
admin.site.register(Contact, ContactAdmin)

class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('id','user','email','is_active', 'subscribed_at')
admin.site.register(NewsLetter, NewsletterAdmin)

class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'post', 'comment', 'action', 'created_at')
admin.site.register(ActivityLog, ActivityLogAdmin)
