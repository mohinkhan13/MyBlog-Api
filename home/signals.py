from django.db.models.signals import post_save
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Post, PostStats, Comment

@receiver(post_save, sender=Post)
def create_post_stats(sender, instance, created, **kwargs):
    if created:
        PostStats.objects.create(post=instance)

@receiver(post_migrate)
def create_missing_post_stats(sender, **kwargs):
    if sender.name == "home":  # Ensure it runs only for 'home' app
        posts = Post.objects.all()
        for post in posts:
            if not PostStats.objects.filter(post=post).exists():
                PostStats.objects.create(post=post)

@receiver(post_save, sender=Comment)
def update_comment_count(sender, instance, **kwargs):   
    post_stats, created = PostStats.objects.get_or_create(post=instance.post)    
    new_comment_count = Comment.objects.filter(post=instance.post).count()
    post_stats.comments = new_comment_count
    post_stats.save()

