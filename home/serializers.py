from rest_framework import serializers
from .models import CustomUser, PostCategory, Post, PostStats, Reply, Comment, Contact, NewsLetter
from django.utils.text import slugify
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['is_superuser'] = user.is_superuser
        token['is_staff'] = user.is_staff
        return token
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},  # Optional for updates
            'email': {'required': True}
        }
        read_only_fields = ['id', 'joined_on']  # Removed invalid 'is_logged_in'

    def validate_email(self, value):
        # Skip uniqueness check if updating and email is unchanged
        if self.instance and self.instance.email == value:
            return value
        # Check uniqueness for new email
        if CustomUser.objects.filter(email=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Email already exists.")
        if "@" not in value or not value.endswith(('.com', '.in')):
            raise serializers.ValidationError("Invalid email format.")
        return value

    def validate_password(self, value):
        if value:  # Only validate if password is provided
            if len(value) < 8:
                raise serializers.ValidationError("Password should be at least 8 characters long.")
            if not any(char.isdigit() for char in value):
                raise serializers.ValidationError("Password should contain at least one digit.")
            if not any(char.isalpha() for char in value):
                raise serializers.ValidationError("Password should contain at least one letter.")
        return value

    def validate_fname(self, value):
        if len(value) < 2 or len(value) > 50:
            raise serializers.ValidationError("First name should be between 2 and 50 characters long.")
        return value
    
    def validate_lname(self, value):
        if len(value) < 2 or len(value) > 50:
            raise serializers.ValidationError("Last name should be between 2 and 50 characters long.")
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        # Handle password separately
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class PostSerializer(serializers.ModelSerializer):
    categoryName = serializers.CharField(source="category.name", read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'status', 'category', 'tags', 'image', 'author', 'slug', 'created_at', 'updated_at', 'categoryName']
        read_only_fields = ['author', 'slug', 'created_at', 'updated_at', 'categoryName']
    
    def create(self, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['title'])
        return super().create(validated_data)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCategory
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "user"]

    def get_user(self, obj):
        if obj.user:
            return {
                "email": obj.user.email,
                "username": f"{obj.user.fname} {obj.user.lname}"
            }
        return {"email": "Anonymous", "username": "Anonymous"}

class ReplySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Reply
        fields = "__all__"
        read_only_fields = ["id", "created_at", "user"]

    def get_user(self, obj):
        if obj.user:
            return {
                "email": obj.user.email,
                "username": f"{obj.user.fname} {obj.user.lname}"
            }
        return {"email": "Anonymous", "username": "Anonymous"}

class PostStatsSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    liked_by = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    class Meta:
        model = PostStats
        fields = '__all__'
        read_only_fields = ['id']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

class NewsletterSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = NewsLetter
        fields = '__all__'
        read_only_fields = ['id', 'subscribed_at']

    def get_user(self, obj):
        if obj.user:
            return {
                "email": obj.user.email,
                "fname": obj.user.fname,  # Explicitly include fname
                "lname": obj.user.lname,  # Explicitly include lname
                "username": f"{obj.user.fname} {obj.user.lname}"
            }
        return {"email": obj.email, "username": "N/A"}