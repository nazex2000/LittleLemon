from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User, Group
from .permissions import IsManager
from .serializers import CategorySerializer, MenuItemSerializer, UserSerializer
from .models import Category, MenuItem

# Create your views here.

class UserRoleView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    queryset = Category.objects.all()
    serializer_class = UserSerializer
    def get_queryset(self):
        group_name = self.kwargs['group_name']
        group = Group.objects.get(name=group_name)
        return group.user_set.all()
    def perform_create(self, serializer):
        group_name = self.kwargs['group_name']
        group = Group.objects.get(name=group_name)
        user = serializer.save()
        user.groups.add(group)

class UserRoleDetailView(DestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    #create a delete method that will remove the user from the group named in the URL
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        try:
            group_name = self.kwargs['group_name']
            group = Group.objects.get(name=group_name)
            user.groups.remove(group)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_200_OK)

class CategoryView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

class MenuItemView(ListCreateAPIView):
    serializer_class = MenuItemSerializer
    queryset = MenuItem.objects.all()

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [IsAuthenticated]
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, IsManager]
        return super().get_permissions()

class MenuItemDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = MenuItemSerializer
    queryset = MenuItem.objects.all()

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [IsAuthenticated]
        if self.request.method in ['PUT', 'DELETE', 'PATCH']:
            self.permission_classes = [IsAuthenticated, IsManager]
        return super().get_permissions()