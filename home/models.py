from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.text import slugify
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core import validators

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    fname = models.CharField(max_length=100)
    lname = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    joined_on = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fname', 'lname']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

class PostCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='category_images/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            with transaction.atomic():
                base_slug = slugify(self.name)
                slug = base_slug
                counter = 1
                while PostCategory.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        if self.image:
            if self.image.size > 5*1024*1024:  # 5MB लिमिट
                raise ValidationError("Image size should not exceed 5MB.")
            if not self.image.name.endswith(('.jpg', '.jpeg', '.png')):
                raise ValidationError("Only JPG and PNG images are allowed.")

    def __str__(self):
        return self.name

class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('publish', 'Publish'),
        ('scheduled', 'Scheduled'),
    ]
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    category = models.ForeignKey(PostCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Enter tags separated by commas")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            with transaction.atomic():
                base_slug = slugify(self.title)
                slug = base_slug
                counter = 1
                while Post.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        if self.image:
            if self.image.size > 5*1024*1024: 
                raise ValidationError("Image size should not exceed 5MB.")
            if not self.image.name.endswith(('.jpg', '.jpeg', '.png', 'webp')):
                raise ValidationError("Only JPG and PNG images are allowed.")

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments', blank=True, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.email} on {self.post.title}"

class Reply(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.user.email} to {self.comment}"

class PostStats(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='stats')
    views = models.PositiveIntegerField(default=0, db_index=True)
    likes = models.PositiveIntegerField(default=0, db_index=True)
    liked_by = models.ManyToManyField(CustomUser, blank=True, related_name='liked_posts')
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Post Stats for -> {self.post.title}"

class Contact(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="contacts")
    name = models.CharField(max_length=100)
    email = models.EmailField(validators=[validators.validate_email])
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # For timestamp

    def __str__(self):
        return f"Contact from {self.name} - {self.subject}"

class NewsLetter(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="newsletters")
    is_active = models.BooleanField(default=True)
    email = models.EmailField(unique=True, db_index=True)
    subscribed_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.user} - {self.email}" if self.user else self.email
    
class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('VIEW_POST', 'View Post'),
        ('LIKE_POST', 'Like Post'),
        ('COMMENT', 'Comment'),
        ('REPLY', 'Reply'), 
        ('SHARE_POST', 'Share Post'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('ADMIN_LOGIN', 'Admin Login'),
        ('CREATE_POST', 'Create Post'),
        ('EDIT_POST', 'Edit Post'),
        ('DELETE_POST', 'Delete Post'),
        ('SUBSCRIBE_NEWSLETTER', 'Subscribe to Newsletter'),
        ('CONTACT_SUBMISSION', 'Contact Form Submission'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="activity_logs")
    post = models.ForeignKey('Post', on_delete=models.SET_NULL, null=True, blank=True, related_name="activity_logs")
    comment = models.ForeignKey('Comment', on_delete=models.SET_NULL, null=True, blank=True, related_name="activity_logs")  # ✅ Added for replies
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    time_spent = models.PositiveIntegerField(null=True, blank=True, help_text="Time spent in seconds")

    def __str__(self):
        return f"{self.user} - {self.action} - {self.post if self.post else ''}"