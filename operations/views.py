from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date, parse_time
from .models import MenuItem, InventoryItem, RecipeRequirement, RestaurantTable, Reservation, Order
from .serializers import (
    MenuItemSerializer, InventoryItemSerializer, RecipeRequirementSerializer,
    RestaurantTableSerializer, ReservationSerializer, OrderSerializer
)

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer

class RecipeRequirementViewSet(viewsets.ModelViewSet):
    queryset = RecipeRequirement.objects.all()
    serializer_class = RecipeRequirementSerializer

class RestaurantTableViewSet(viewsets.ModelViewSet):
    queryset = RestaurantTable.objects.all()
    serializer_class = RestaurantTableSerializer

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    
    @action(detail=False, methods=['get'])
    def availability(self, request):
        date_str = request.query_params.get('date')
        start_time_str = request.query_params.get('start_time')
        end_time_str = request.query_params.get('end_time')
        
        if not all([date_str, start_time_str, end_time_str]):
            return Response({"error": "Please provide date, start_time, and end_time parameters."}, status=400)
            
        date = parse_date(date_str)
        start_time = parse_time(start_time_str)
        end_time = parse_time(end_time_str)
        
        if not all([date, start_time, end_time]):
            return Response({"error": "Invalid date or time format."}, status=400)

        # Find tables that have overlapping reservations
        reserved_tables = Reservation.objects.filter(
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).values_list('table_id', flat=True)
        
        # Get all other tables
        available_tables = RestaurantTable.objects.exclude(id__in=reserved_tables)
        serializer = RestaurantTableSerializer(available_tables, many=True)
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
