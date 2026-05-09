from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MenuItemViewSet, InventoryItemViewSet, RecipeRequirementViewSet,
    RestaurantTableViewSet, ReservationViewSet, OrderViewSet
)

router = DefaultRouter()
router.register(r'menu', MenuItemViewSet)
router.register(r'inventory', InventoryItemViewSet)
router.register(r'recipe-requirements', RecipeRequirementViewSet)
router.register(r'tables', RestaurantTableViewSet)
router.register(r'reservations', ReservationViewSet)
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
