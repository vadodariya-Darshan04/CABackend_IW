from rest_framework import serializers
from .models import MenuItem, InventoryItem, RecipeRequirement, RestaurantTable, Reservation, Order, OrderItem

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = '__all__'

class RecipeRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeRequirement
        fields = '__all__'

class RestaurantTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantTable
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'
        
    def validate(self, data):
        # Check if table is available for the given date and time
        table = data['table']
        date = data['date']
        start_time = data['start_time']
        end_time = data['end_time']
        
        if start_time >= end_time:
            raise serializers.ValidationError("End time must be after start time.")
            
        overlapping_reservations = Reservation.objects.filter(
            table=table,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        if overlapping_reservations.exists():
            raise serializers.ValidationError("This table is already reserved for the requested time period.")
            
        return data

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.ReadOnlyField(source='menu_item.name')

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_name', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'table', 'status', 'created_at', 'items']
        
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            menu_item = item_data['menu_item']
            quantity = item_data['quantity']
            
            # Create OrderItem
            OrderItem.objects.create(order=order, menu_item=menu_item, quantity=quantity)
            
            # Deduct from Inventory
            requirements = RecipeRequirement.objects.filter(menu_item=menu_item)
            for req in requirements:
                inventory_item = req.inventory_item
                total_required = req.quantity_required * quantity
                
                # Deduct inventory
                inventory_item.quantity_in_stock -= total_required
                inventory_item.save()
                
        return order
