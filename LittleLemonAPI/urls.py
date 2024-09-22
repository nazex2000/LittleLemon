from django.urls import path, include
from .views import UserRoleView

urlpatterns = [
    path('users/<int:id>/groups/', UserRoleView.as_view()),
]