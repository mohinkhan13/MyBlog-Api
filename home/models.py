from django.db import models
from django.utils.text import slugify

# Create your models here.
class CustomUser(models.Model):
    fname = models.CharField(max_length=100)
    lname = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=128)
    phone = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)
    is_logged_in = models.BooleanField(default=False)
    joined_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.fname
    
class PostCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='category_images/', null=True, blank=True, default=None)

    def __str__(self):
        return self.name

class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('publish', 'Publish'),
        ('sheduled', 'Sheduled'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    category = models.ForeignKey(PostCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Enter tags separated by commas")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    image = models.ImageField(upload_to='post_images/', null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Create Slug With title
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"

class Reply(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.name} to {self.comment.name}"

class PostStats(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"PostStats for {self.post.title}"