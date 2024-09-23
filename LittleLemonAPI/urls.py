from django.urls import path, include
from .views import UserRoleView, UserRoleDetailView,CategoryView, MenuItemView, MenuItemDetailView, CartView, OrderView, OrderDetailView

urlpatterns = [
    path('groups/<str:group_name>/users', UserRoleView.as_view()),
    path('groups/<str:group_name>/users/<int:pk>', UserRoleDetailView.as_view()),
    path('categories', CategoryView.as_view()),
    path('menu-items', MenuItemView.as_view()),
    path('menu-items/<int:pk>', MenuItemDetailView.as_view()),
    path('cart/menu-items', CartView.as_view()),
    path('orders', OrderView.as_view()),
    path('orders/<int:pk>', OrderDetailView.as_view()),

]