from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User, Group
from .permissions import IsManager

# Create your views here.

class UserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsManager]
    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
            role = user.groups.all()[0]
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except IndexError:
            return Response({'message': 'User has no role'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'role': role.name}, status=status.HTTP_200_OK)

    def put(self, request, id):
        try:
            user = User.objects.get(id=id)
            group_id = request.data['role_id']
            new_group = Group.objects.get(id=group_id)
            user.groups.clear()
            user.groups.add(new_group)
            user.save()
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({'message': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'message': 'Role Updated'}, status=status.HTTP_200_OK)
