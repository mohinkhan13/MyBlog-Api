from django.db.models.signals import post_save
from django.db.models.signals import *
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Post, PostStats, ActivityLog, Comment, NewsLetter, Contact, Reply
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

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



@receiver(post_save, sender=PostStats)
def log_post_view(sender, instance, **kwargs):
    """
    Logs when a user views a post. The frontend should send the time spent per post.
    """
    if instance.views > 0:  # Check if view count increased
        ActivityLog.objects.create(
            user=instance.post.author,
            post=instance.post,
            action="VIEW_POST",
            time_spent=instance.views,  # Assuming view count equals seconds spent
        )


### 2️⃣ Log Post Creation, Update, and Deletion (Admin Actions) ###
@receiver(post_save, sender=Post)
def log_admin_post_activity(sender, instance, created, **kwargs):
    action = "CREATE_POST" if created else "EDIT_POST"
    ActivityLog.objects.create(
        user=instance.author,
        action=action,
        post=instance
    )

@receiver(post_delete, sender=Post)
def log_admin_post_deletion(sender, instance, **kwargs):
    ActivityLog.objects.create(
        user=instance.author,
        action="DELETE_POST",
        post=instance
    )


### 3️⃣ Log Likes ###
@receiver(m2m_changed, sender=PostStats.liked_by.through)
def log_like_activity(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        user = CustomUser.objects.get(pk=list(pk_set)[0])
        ActivityLog.objects.create(
            user=user,
            action="LIKE_POST",
            post=instance.post
        )


### 4️⃣ Log Comments ###
@receiver(post_save, sender=Comment)
def log_comment_activity(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.user,
            action="COMMENT",
            post=instance.post
        )


### 5️⃣ Log Shares ###
@receiver(post_save, sender=PostStats)
def log_share_activity(sender, instance, **kwargs):
    if instance.shares > 0:
        ActivityLog.objects.create(
            user=instance.post.author,
            action="SHARE_POST",
            post=instance.post
        )


### 6️⃣ Log Login & Logout ###
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        action="LOGIN",
        ip_address=request.META.get('REMOTE_ADDR')
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        action="LOGOUT",
        ip_address=request.META.get('REMOTE_ADDR')
    )


### 7️⃣ Log Admin Logins ###
@receiver(user_logged_in)
def log_admin_login(sender, request, user, **kwargs):
    if user.is_staff or user.is_superuser:
        ActivityLog.objects.create(
            user=user,
            action="ADMIN_LOGIN",
            ip_address=request.META.get('REMOTE_ADDR')
        )


### 8️⃣ Log Newsletter Subscription ###
@receiver(post_save, sender=NewsLetter)
def log_newsletter_subscription(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.user,
            action="SUBSCRIBE_NEWSLETTER"
        )


### 9️⃣ Log Contact Form Submission ###
@receiver(post_save, sender=Contact)
def log_contact_submission(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.user if instance.user else None,
            action="CONTACT_SUBMISSION"
        )

@receiver(post_save, sender=Reply)
def log_reply_activity(sender, instance, created, **kwargs):
    """
    Logs when a user replies to a comment.
    """
    if created:
        ActivityLog.objects.create(
            user=instance.user,
            action="REPLY",
            post=instance.comment.post,  # ✅ Logs the post where the reply was made
            comment=instance.comment  # ✅ Links to the specific comment being replied to
        )