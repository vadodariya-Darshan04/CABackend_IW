from django.contrib import admin
from .models import MenuItem, InventoryItem, RecipeRequirement, RestaurantTable, Reservation, Order, OrderItem

class RecipeRequirementInline(admin.TabularInline):
    model = RecipeRequirement
    extra = 1

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available')
    inlines = [RecipeRequirementInline]

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity_in_stock', 'unit_of_measure')

@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'seating_capacity')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'table', 'date', 'start_time', 'end_time')
    list_filter = ('date', 'table')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'table')
    inlines = [OrderItemInline]
