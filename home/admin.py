from django.contrib import admin
from .models import CustomUser, PostCategory,Post, PostStats , Comment , Reply

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(PostCategory)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'category', 'status', 'created_at', 'updated_at')
admin.site.register(Post, PostAdmin)
class PostStatsAdmin(admin.ModelAdmin):
    list_display = ('id','post', 'views', 'likes', 'comments', 'shares')

admin.site.register(PostStats, PostStatsAdmin)
admin.site.register(Comment)
admin.site.register(Reply)
