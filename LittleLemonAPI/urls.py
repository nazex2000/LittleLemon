from django.urls import path, include
from .views import UserRoleView, UserRoleDetailView,CategoryView, MenuItemView, MenuItemDetailView

urlpatterns = [
    path('groups/<str:group_name>/users/', UserRoleView.as_view()),
    path('groups/<str:group_name>/users/<int:pk>/', UserRoleDetailView.as_view()),
    path('categories/', CategoryView.as_view()),
    path('menu-items/', MenuItemView.as_view()),
    path('menu-items/<int:pk>/', MenuItemDetailView.as_view()),
]