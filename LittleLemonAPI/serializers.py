from .models import Category, MenuItem
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User, Group

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']
class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'groups']
    extra_kwargs = {
        'password': {'write_only': True},
    }

class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class MenuItemSerializer(ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']
    def create(self, validated_data):
        category_id = validated_data.pop('category_id')
        category = Category.objects.get(id=category_id)
        menu_item = MenuItem.objects.create(category=category, **validated_data)
        return menu_item
    extra_kwargs = {
        'price': {'error_messages': {'max_value': 'Price must be less than 1000'}},
        'title': {
            'validators': [
                UniqueValidator(queryset=MenuItem.objects.all(), message='This item already exists')
            ],
        }
    }



