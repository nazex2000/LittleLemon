from .models import Category, MenuItem, Cart, Order, OrderItem
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

class CartSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'created_at', 'updated_at']
    def validate(self, data):
        user = data['user']
        menuitem = data['menuitem']
        if Cart.objects.filter(user=user, menuitem=menuitem).exists():
            raise serializers.ValidationError('This item is already in the cart')
        return data

class OrderSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)
    delivery_crew = UserSerializer(read_only=True)
    class Meta:
        model = Order
        fields = '__all__'

class OrderItemSerializer(ModelSerializer):
    order = OrderSerializer(read_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = '__all__'

