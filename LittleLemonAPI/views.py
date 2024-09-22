from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User, Group
from .permissions import IsManager, IsCustomer, IsDeliveryCrew
from .serializers import CategorySerializer, MenuItemSerializer, UserSerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.db.utils import IntegrityError
from rest_framework.filters import SearchFilter
from django.core.paginator import Paginator, EmptyPage
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

# Create your views here.

class UserRoleView(ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated, IsManager]
    queryset = Category.objects.all()
    serializer_class = UserSerializer
    def get_queryset(self):
        group_name = self.kwargs['group_name']
        group = Group.objects.get(name=group_name)
        return group.user_set.all()
    def post(self, request, *args, **kwargs):
        try:
            group_name = self.kwargs['group_name']
            group = Group.objects.get(name=group_name)
            user = User.objects.get(username=request.data['username'])
            user.groups.add(group)
            return Response(status=status.HTTP_201_CREATED)
        except KeyError:
            return Response({'error': 'Username field is required'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

class UserRoleDetailView(DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
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
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

class MenuItemView(ListCreateAPIView):
    serializer_class = MenuItemSerializer
    queryset = MenuItem.objects.all()
    filter_backends = [SearchFilter]
    search_fields = ['title', 'category__name']
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [IsAuthenticated]
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, IsManager]
        return super().get_permissions()

    def get_queryset(self):
        category = self.request.query_params.get('category', None)
        price_from = self.request.query_params.get('price_from', None)
        price_to = self.request.query_params.get('price_to', None)
        ordering = self.request.query_params.get('ordering', None)
        perpage = self.request.query_params.get('perpage', None)
        page = self.request.query_params.get('page', None)
        queryset = MenuItem.objects.all()
        if category:
            queryset = queryset.filter(category__id=category)
        if price_from:
            queryset = queryset.filter(price__gte=price_from)
        if price_to:
            queryset = queryset.filter(price__lte=price_to)
        if ordering:
            ordering_fieds = ordering.split(',')
            queryset = queryset.order_by(*ordering_fieds)
        paginator = Paginator(queryset, perpage)
        try:
            queryset = paginator.page(number=page)
        except EmptyPage:
            queryset = paginator.page(number=paginator.num_pages)
        return queryset

class MenuItemDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = MenuItemSerializer
    queryset = MenuItem.objects.all()
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [IsAuthenticated]
        if self.request.method in ['PUT', 'DELETE', 'PATCH']:
            self.permission_classes = [IsAuthenticated, IsManager]
        return super().get_permissions()

class CartView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user)
        serializer = CartSerializer(cart, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = User.objects.get(username=request.user)
        try:
            menuitem = MenuItem.objects.get(id=request.data['menuitem_id'])
            quantity = request.data['quantity']
            unit_price = menuitem.price
            cart_item = Cart.objects.create(user=user, menuitem=menuitem, quantity=quantity, unit_price=unit_price)
            return Response(status=status.HTTP_201_CREATED)
        except KeyError:
            return Response({'error': 'menuitem_id and quantity fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        except MenuItem.DoesNotExist:
            return Response({'error': 'Menu item not found'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'error': 'This item is already in the cart'}, status=status.HTTP_400_BAD_REQUEST)


class OrderView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, (IsCustomer | IsManager | IsDeliveryCrew)]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        user = self.request.user
        datav= []
        if user.groups.filter(name='customers').exists():
            orders = Order.objects.filter(user=user)
        elif user.groups.filter(name='managers').exists():
            orders = Order.objects.all()
        elif user.groups.filter(name='delivery-crews').exists():
            orders = Order.objects.filter(delivery_crew=user)
        for order in orders:
            order_items = OrderItem.objects.filter(order=order)
            order_items_serializer = OrderItemSerializer(order_items, many=True)
            order_serializer = OrderSerializer(order)
            data = {
                'order': order_serializer.data,
                'order_items': order_items_serializer.data
            }
            datav.append(data)
        return Response(datav)

    def post(self, request):
        user = User.objects.get(username=request.user)
        try:
            total = 0
            order = Order.objects.create(user=user, total=0)
            cart = Cart.objects.filter(user=user)
            for item in cart:
                total += item.unit_price * item.quantity
                OrderItem.objects.create(order=order, menuitem=item.menuitem, quantity=item.quantity, unit_price=item.unit_price, total=item.unit_price * item.quantity)

            order.total = total
            order.save()
            cart.delete()

            order_Serializer = OrderSerializer(order)
            return Response(order_Serializer.data, status=status.HTTP_201_CREATED)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [IsAuthenticated]
        if self.request.method in ['PUT', 'DELETE']:
            self.permission_classes = [IsAuthenticated, IsManager]
        if self.request.method == 'PATCH':
            self.permission_classes = [IsAuthenticated, (IsManager | IsDeliveryCrew)]
        return super().get_permissions()

    def get(self, request, pk):
        user = request.user
        try:
            order = Order.objects.get(id=pk)
            #only the user who created the order can view it
            if order.user != user:
                return Response({'error': 'You are not authorized to view this order'}, status=status.HTTP_403_FORBIDDEN)
            order_items = OrderItem.objects.filter(order=order)
            order_items_serializer = OrderItemSerializer(order_items, many=True)
            order_serializer = OrderSerializer(order)
            data = {
                'order': order_serializer.data,
                'order_items': order_items_serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    #defs for put and patch
    def put(self, request, pk):
        user = request.user
        try:
            order = Order.objects.get(id=pk)
            if order.delivery_crew != None and order.status == True:
                return Response({'error': 'Order has been delivered'}, status=status.HTTP_400_BAD_REQUEST)
            delivery_crew = User.objects.get(username=request.data['delivery_crew'])
            if delivery_crew.groups.filter(name='delivery-crews').exists() == False:
                return Response({'error': 'User is not a delivery crew'}, status=status.HTTP_400_BAD_REQUEST)
            stts = request.data['status']
            order.delivery_crew = delivery_crew
            order.status = stts
            order.save()
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)
        except KeyError:
            return Response({'error': 'delivery_crew and status fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        user = request.user
        try:
            order = Order.objects.get(id=pk)
            if order.delivery_crew != None and order.status == True:
                return Response({'error': 'Order has been delivered'}, status=status.HTTP_400_BAD_REQUEST)
            stts = request.data['status']
            order.status = stts
            order.save()
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)
        except KeyError:
            return Response({'error': 'status field is required'}, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        user = request.user
        try:
            order = Order.objects.get(id=pk)
            order.delete()
            return Response(status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)



