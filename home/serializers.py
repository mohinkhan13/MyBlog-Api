from rest_framework import serializers
from .models import CustomUser, PostCategory, Post
from django.utils.text import slugify

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'
    
    def create(self, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['title'])  # Generate slug
        return super().create(validated_data)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCategory
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
            }
        read_only_fields = ['id','is_admin', 'is_logged_in', 'joined_on']

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        if "@" not in value or not value.endswith(('.com', '.in')):
            raise serializers.ValidationError("Invalid email format.")        
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password should be at least 8 characters long.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password should contain at least one digit.")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError("Password should contain at least one letter.")
        return value
    
    def validate_phone(self, value):
        if not value.isdigit() or not (10 <= len(value) <= 13):
            raise serializers.ValidationError("Invalid phone number format.")
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
        # hash the password before saving using make_password
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    
